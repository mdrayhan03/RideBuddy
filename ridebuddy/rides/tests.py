from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from accounts.models import Student, Vehicle, Community
from rides.models import Ride, OwnerCommission
from rides.services.ride_commission_service import OwnerCommissionService

User = get_user_model()

class OwnerCommissionModelTest(TestCase):
    def setUp(self):
        # Create standard test hierarchy
        self.community = Community.objects.create(name="Test University", short_name="TU")
        
        self.user = User.objects.create_user(
            username="owner_student",
            email="owner@tu.edu",
            password="testpassword123",
            is_student=True
        )
        
        self.vehicle = Vehicle.objects.create(
            vehicle_type="car",
            vehicle_model="Toyota Corolla",
            vehicle_plate_no="DHAKA-METRO-KA-12-3456",
            capacity=4,
            ac_available=True
        )
        
        self.student = Student.objects.create(
            user=self.user,
            id_no="2026-1-60-001",
            community=self.community,
            has_vehicle=True,
            vehicle=self.vehicle
        )
        
        self.commission = OwnerCommission.objects.create(
            owner=self.student,
            from_date=date(2026, 5, 1),
            to_date=date(2026, 5, 7),
            total_ride_fare=Decimal("500.00"),
            commission_amount=Decimal("50.00"),
            payment_status="due"
        )

    def test_commission_str_method_fixes_bug(self):
        """
        Assures that the str representation returns the correct owner username.
        If the rider-attribute bug exists, this test will crash with AttributeError.
        """
        expected_str = f"Payment {self.commission.id} by owner_student"
        self.assertEqual(str(self.commission), expected_str)

    def test_commission_bkash_instructions(self):
        """Verify dynamic bKash instruction payload matching."""
        self.commission.payment_method = "bkash"
        self.commission.save()
        instructions = self.commission.get_instructions
        self.assertEqual(instructions["title"], "Pay via bKash Personal")
        self.assertIn("017XXXXXXXX", instructions["number"])

    def test_commission_nagad_instructions(self):
        """Verify dynamic Nagad instruction payload matching."""
        self.commission.payment_method = "nagad"
        self.commission.save()
        instructions = self.commission.get_instructions
        self.assertEqual(instructions["title"], "Pay via Nagad")
        self.assertIn("018XXXXXXXX", instructions["number"])


class OwnerPaymentSystemTest(TestCase):
    def setUp(self):
        self.community = Community.objects.create(name="East West University", short_name="EWU")
        self.user = User.objects.create_user(
            username="payment_owner", email="owner@ewu.edu", password="pass", is_student=True
        )
        self.vehicle = Vehicle.objects.create(
            vehicle_type="car", vehicle_model="Toyota Fielder", vehicle_plate_no="METRO-KA-99-9999", capacity=4
        )
        self.owner = Student.objects.create(
            user=self.user, id_no="PAY-001", community=self.community, has_vehicle=True, vehicle=self.vehicle
        )

        # Create a completed ride that ended yesterday
        yesterday = timezone.now() - timedelta(days=1)
        self.completed_ride = Ride.objects.create(
            vehicle=self.vehicle,
            status="completed",
            dropped_time=yesterday,
            total_fare=Decimal("1200.00"),
            commission_rate=Decimal("10.00") # 10%
        )

    def test_commission_generation_and_payment_flow(self):
        """
        Tests calculation of commission amounts and status lifecycle updates.
        """
        # 1. Generate commission
        commission = OwnerCommissionService.create_commission(self.owner)
        self.assertIsNotNone(commission)
        self.assertEqual(commission.total_ride_fare, Decimal("1200.00"))
        
        # Commission is 10% of 1200.00 = 120.00
        self.assertEqual(commission.commission_amount, Decimal("120.00"))
        self.assertEqual(commission.payment_status, "due")

        # 2. Process payment via bKash Personal
        tx_id = "BKASH12345XYZ"
        success, msg = OwnerCommissionService.process_payment(
            commission=commission,
            payment_method="bkash",
            payment_id=tx_id
        )
        self.assertTrue(success)
        
        # Verify status changes
        commission.refresh_from_db()
        self.assertEqual(commission.payment_status, "paid")
        self.assertEqual(commission.payment_id, tx_id)
        self.assertEqual(commission.payment_method, "bkash")
        self.assertIsNotNone(commission.payment_date)

    def test_double_payment_prevention(self):
        """Ensure a paid commission cannot be repaid."""
        commission = OwnerCommissionService.create_commission(self.owner)
        self.assertIsNotNone(commission)
        OwnerCommissionService.process_payment(commission, "nagad", "NAGAD999")
        
        # Attempt to pay again
        success, msg = OwnerCommissionService.process_payment(commission, "rocket", "ROCKET999")
        self.assertFalse(success)
        self.assertEqual(msg, "Commission already paid.")
