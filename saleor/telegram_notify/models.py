import random
import string

from django.contrib.auth import get_user_model
from django.db import models


class ChatStates:
    undefined = '_undefined'
    waiting_for_email = '_waiting_for_email'
    user_is_not_confirmed = '_user_is_not_confirmed'
    authorized_admin = '_authorized_admin'


class Chat(models.Model):
    CONFIRM_CODE_MAX_LENGTH = 6
    RESEND_CODE_AVAILABLE_AFTER_MINUTES = 5
    STATE_CHOICES = (
        (ChatStates.undefined, ChatStates.undefined),
        (ChatStates.user_is_not_confirmed, ChatStates.user_is_not_confirmed),
        (ChatStates.authorized_admin, ChatStates.authorized_admin))

    user = models.OneToOneField(get_user_model(), null=True, on_delete=models.CASCADE)
    chat_id = models.CharField(max_length=200)
    confirm_code = models.CharField(max_length=CONFIRM_CODE_MAX_LENGTH)
    code_confirmed = models.BooleanField(default=False)
    last_code_send_time = models.DateTimeField(null=True)
    state = models.CharField(max_length=30,
                             default=ChatStates.undefined,
                             choices=STATE_CHOICES)

    def save(self, **kwargs) -> None:
        if not self.pk:
            self.confirm_code = self._generate_random_confirm_code()
        super().save(**kwargs)

    def _generate_random_confirm_code(self):
        letters = string.ascii_lowercase
        result_str = ''.join(
            random.choice(letters) for _ in range(self.CONFIRM_CODE_MAX_LENGTH))

        return result_str

    def regenerate_confirm_code(self):
        self.confirm_code = self._generate_random_confirm_code()
        self.save()
