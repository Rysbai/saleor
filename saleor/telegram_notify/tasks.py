from ..celeryconf import app


from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template import Template, Context


@app.task
def send_bot_confirm_code(code: str, email: str):
    site = Site.objects.get_current()
    html = """
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@500&display=swap" rel="stylesheet">

        <div style="font-family: 'Inter', sans-serif;">
          <h2 >
            Доброго времени суток!
          </h2>
          <p>
            <b>Ваш код для подтверждения: </b> {{ code }}
          </p>
          <small style="color: #21125E;">*Код актуален в течении дня<small/>
        </div>
    """
    message = Template(html).render(Context({
        "code": code,
    }))

    send_mail(
        subject=f'Администрация сайта {site.name}',
        message=None,
        html_message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email, ]
    )
