from datetime import timedelta

from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from schedule.models import Event

from appointments.models import Appointment


@receiver(post_delete, sender=Appointment)
def event_delete(sender, instance, **kwargs):
    """
    When an appointment is deleted, we proceed to delete the Event Object that it references
    """
    try:
        if instance.event:
            this_event = instance.event
            this_event.delete()
    except Event.DoesNotExist:
        pass


@receiver(pre_save, sender=Event)
def event_changed(sender, instance, **kwargs):
    """
    if the event has been updated, we want to do a few things
        1. if the new start time is more than half a day greater than original
        then allow reminders to be sent (if they were turned off)
    """
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        # ensure that end time is not before start time
        if instance.end <= instance.start:
            instance.end = instance.start + timedelta(minutes=15)
    else:
        if not obj.start == instance.start:  # Field has changed
            if instance.start > obj.start:
                diff = instance.start - obj.start
                if diff > timedelta(hours=12):
                    appointment = obj.appointment_set.first()
                    if appointment:
                        appointment.no_reminders = False
                        appointment.save()
