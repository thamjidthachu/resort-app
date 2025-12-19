from django.conf import settings
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response

from utils import send_email_message
import logging
contact_logger = logging.getLogger('system_logs')

from apps.contacts.models import ContactMessage
from apps.contacts.serializers import ContactMessageSerializer


class ContactMessageView(ListCreateAPIView):
    permission_classes = []
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            contact_logger.info(f"Contact message created: subject={request.data.get('subject')}, email={request.data.get('email')}")
            send_email_message.delay(
                subject=f"New Enquiry Received | {request.data.get('subject')} | Azure Horizon",
                template_name="admin-enquiry-notification.html",
                context=request.data,
                recipient_list=[settings.DEFAULT_FROM_EMAIL]
            )
            send_email_message.delay(
                subject=f"Received Your Enquiry | {request.data.get('subject')} | Azure Horizon",
                template_name="contact-response.html",
                context=request.data,
                recipient_list=[request.data.get('email')]
            )
            return Response({"message": "Your contact has been submitted successfully"}, status=status.HTTP_201_CREATED)
        else:
            contact_logger.warning(f"Contact message creation failed: errors={serializer.errors}")
            return Response({"error": "Something went wrong. Try again later"}, status=status.HTTP_400_BAD_REQUEST)
