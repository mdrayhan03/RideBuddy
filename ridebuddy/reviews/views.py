from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .models import RiderReview, VehicleReview, PassengerReview, PlatformReview, StudentReview

def rating_view(request):
    return render(request, 'rating.html')

@login_required
@csrf_exempt
def submit_review_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            review_id = data.get('review_id')
            review_type = data.get('type')
            rating = data.get('rating')
            review_text = data.get('review')
            status_update = data.get('status', 'done')

            if review_type == 'rider':
                obj = RiderReview.objects.get(id=review_id)
            elif review_type == 'vehicle':
                obj = VehicleReview.objects.get(id=review_id)
            elif review_type == 'passenger':
                obj = PassengerReview.objects.get(id=review_id)
            elif review_type == 'platform':
                obj = PlatformReview.objects.get(id=review_id)
            elif review_type == 'student':
                obj = StudentReview.objects.get(id=review_id)
            else:
                return JsonResponse({"success": False, "message": "Invalid review type"})

            if status_update == 'cancel':
                obj.status = 'cancel'
                obj.save()
            else:
                if rating in [None, 0, '0', '']:
                    return JsonResponse({"success": False, "message": "Please select a rating."})
                obj.rating = rating
                obj.review = review_text
                obj.status = 'done'
                obj.save()

            return JsonResponse({"success": True, "message": "Review saved"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False, "message": "POST required"})
