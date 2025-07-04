import datetime
import logging
import re
import subprocess

from django.utils import timezone
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.forms import ModelForm
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import pre_save
from django.template import RequestContext, Template, TemplateSyntaxError
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from django.contrib.postgres.fields import HStoreField
from django_s3.storage import S3Storage

from mezzanine.core.fields import FileField, RichTextField
from mezzanine.core.models import Orderable, SiteRelated
from mezzanine.core.request import current_request
from mezzanine.pages.models import Page
from mezzanine.utils.models import upload_to

from sorl.thumbnail import ImageField as ThumbnailImageField
from theme.utils import get_upload_path_userprofile
from theme.enums import QuotaStatus


DEFAULT_COPYRIGHT = '&copy; {% now "Y" %} {{ settings.SITE_TITLE }}'
logger = logging.getLogger(__name__)


class SiteConfiguration(SiteRelated):
    """
    A model to edit sitewide content
    """

    col1_heading = models.CharField(max_length=200, default="Contact us")
    col1_content = RichTextField()
    col2_heading = models.CharField(max_length=200, default="Follow")
    col2_content = RichTextField(
        blank=True, help_text="If present will override the " "social network icons."
    )
    col3_heading = models.CharField(max_length=200, default="Subscribe")
    col3_content = RichTextField()
    twitter_link = models.CharField(max_length=2000, blank=True)
    facebook_link = models.CharField(max_length=2000, blank=True)
    pinterest_link = models.CharField(max_length=2000, blank=True)
    youtube_link = models.CharField(max_length=2000, blank=True)
    github_link = models.CharField(max_length=2000, blank=True)
    linkedin_link = models.CharField(max_length=2000, blank=True)
    vk_link = models.CharField(max_length=2000, blank=True)
    gplus_link = models.CharField(max_length=2000, blank=True)
    has_social_network_links = models.BooleanField(default=False, blank=True)
    copyright = models.TextField(default=DEFAULT_COPYRIGHT)

    class Meta:
        verbose_name = _("Site Configuration")
        verbose_name_plural = _("Site Configuration")

    def save(self, *args, **kwargs):
        """
        Set has_social_network_links
        """
        if (
            self.twitter_link
            or self.facebook_link
            or self.pinterest_link
            or self.youtube_link
            or self.github_link
            or self.linkedin_link
            or self.vk_link
            or self.gplus_link
        ):
            self.has_social_network_links = True
        else:
            self.has_social_network_links = False
        super(SiteConfiguration, self).save(*args, **kwargs)

    def render_copyright(self):
        """
        Render the footer
        """
        c = RequestContext(current_request())
        try:
            t = Template(self.copyright)
        except TemplateSyntaxError:
            return ""
        return t.render(c)


class HomePage(Page):
    """
    A home page page type
    """

    MESSAGE_TYPE_CHOICES = (("warning", "Warning"), ("information", "Information"))
    heading = models.CharField(max_length=100)
    slide_in_one_icon = models.CharField(max_length=50, blank=True)
    slide_in_one = models.CharField(max_length=200, blank=True)
    slide_in_two_icon = models.CharField(max_length=50, blank=True)
    slide_in_two = models.CharField(max_length=200, blank=True)
    slide_in_three_icon = models.CharField(max_length=50, blank=True)
    slide_in_three = models.CharField(max_length=200, blank=True)
    header_background = FileField(
        verbose_name=_("Header Background"),
        upload_to=upload_to("theme.HomePage.header_background", "homepage"),
        format="Image",
        max_length=255,
        blank=True,
    )
    header_image = FileField(
        verbose_name=_("Header Image (optional)"),
        upload_to=upload_to("theme.HomePage.header_image", "homepage"),
        format="Image",
        max_length=255,
        blank=True,
        null=True,
    )
    welcome_heading = models.CharField(max_length=100, default="Welcome")
    content = RichTextField()
    recent_blog_heading = models.CharField(max_length=100, default="Latest blog posts")
    number_recent_posts = models.PositiveIntegerField(
        default=3, help_text="Number of recent blog posts to show"
    )

    # The following date fields are used for duration during which the message will be displayed
    message_start_date = models.DateField(
        null=True, help_text="Date from which the message will " "be displayed"
    )
    message_end_date = models.DateField(
        null=True, help_text="Date on which the message will no " "more be displayed"
    )

    # this must be True for the message to be displayed
    show_message = models.BooleanField(default=False, help_text="Check to show message")

    # use message type to change background color of the message
    message_type = models.CharField(
        max_length=100, choices=MESSAGE_TYPE_CHOICES, default="Information"
    )

    class Meta:
        verbose_name = _("Home page")
        verbose_name_plural = _("Home pages")

    @property
    def can_show_message(self):
        if not self.show_message:
            return False
        message = strip_tags(self.content).strip()
        if not message:
            return False
        today = datetime.datetime.combine(datetime.datetime.today(), datetime.time())
        today = timezone.make_aware(today)
        today = today.date()
        if self.message_start_date and self.message_end_date:
            if self.message_start_date <= today <= self.message_end_date:
                return True

        return False


class IconBox(Orderable):
    """
    An icon box on a HomePage
    """

    homepage = models.ForeignKey(
        HomePage, on_delete=models.CASCADE, related_name="boxes"
    )
    icon = models.CharField(
        max_length=50,
        help_text="Enter the name of a font awesome icon, i.e. "
        "fa-eye. A list is available here "
        "http://fontawesome.io/",
    )
    title = models.CharField(max_length=200)
    link_text = models.CharField(max_length=100)
    link = models.CharField(
        max_length=2000,
        blank=True,
        help_text="Optional, if provided clicking the box will go here.",
    )


class QuotaMessage(models.Model):
    # warning_content_prepend prepends the content to form a warning message to be emailed to the
    # user and displayed when the user is logged in;
    # enforce_content_prepend prepends the content to form an enforcement message to inform users
    # when they are over hard limit quota
    warning_content_prepend = models.TextField(
        default="Once your quota reaches 100% you will no "
        "longer be able to create new resources in "
        "HydroShare. "
    )
    enforce_content_prepend = models.TextField(
        default="You can not take further action "
        "because you have exceeded your "
        "quota. "
    )
    quota_usage_info = models.TextField(
        default="Your quota for HydroShare resources is {allocated}{unit}. "
        "You currently have resources that consume {used}{unit}, {percent}% of your quota. "
    )
    content = models.TextField(
        default="You can request additional quota, from your "
        "User Profile. We will try to accommodate "
        "reasonable requests for additional quota. If you have a "
        "large quota request you may need to contribute toward the "
        "costs of providing the additional space you need. "
    )
    # quota soft limit percent value for starting to show quota usage warning. Default is 80%
    soft_limit_percent = models.IntegerField(default=80)
    # quota hard limit percent value for hard quota enforcement. Default is 125%
    published_resource_percent = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0)


class UserQuota(models.Model):
    # ForeignKey relationship makes it possible to associate multiple UserQuota models to
    # a User with each UserQuota model defining quota for a set of S3 zones. By default,
    # the UserQuota model instance defines quota in hydroshareZone,
    # categorized as hydroshare in zone field in UserQuota model, however,
    # another UserQuota model instance could be defined in a third-party federated zone as needed.
    user = models.ForeignKey(
        User,
        editable=False,
        null=False,
        on_delete=models.CASCADE,
        related_name="quotas",
        related_query_name="quotas",
    )

    zone = models.CharField(max_length=100, default="hydroshare")

    class Meta:
        verbose_name = _("User quota")
        verbose_name_plural = _("User quotas")
        unique_together = ("user", "zone")

    def _allocated_value_size_and_unit(self):
        try:
            result = subprocess.run(
                ["mc", "quota", "info", f"{self.zone}/{self.user.userprofile.bucket_name}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
        except (subprocess.CalledProcessError, ValueError, IndexError):
            return settings.DEFAULT_QUOTA_VALUE, settings.DEFAULT_QUOTA_UNIT
        result_split = result.stdout.split(" ")
        unit = result_split[-1].strip()
        unit = unit.replace("i", "")
        size = result_split[-2]
        return float(size), unit

    @property
    def allocated_value(self):
        size, _ = self._allocated_value_size_and_unit()
        return size

    def _convert_unit(self, unit):
        if len(unit) == 2:
            return f'{unit[0]}i{unit[1]}'
        return unit

    def save_allocated_value(self, allocated_value, unit):
        """
        Save the allocated value to the database and update the quota on MinIO.
        """
        try:
            subprocess.run(
                ["mc", "quota", "set", f"{self.zone}/{self.user.userprofile.bucket_name}",
                 "--size", f"{allocated_value}{self._convert_unit(unit)}"],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise ValidationError(f"Error setting quota: {e}")

    def _size_and_unit(self):
        try:
            result = subprocess.run(
                ["mc", "stat", f"{self.zone}/{self.user.userprofile.bucket_name}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
        except (subprocess.CalledProcessError, ValueError, IndexError):
            # return a default value of 0 and default unit
            return float(0), settings.DEFAULT_QUOTA_UNIT
        size_with_unit_str = result.stdout.split("Total size: ")[1].split("\n")[0]
        size_and_unit = size_with_unit_str.split(" ")
        size = size_and_unit[0]
        unit = size_and_unit[1]
        unit = unit.replace("i", "")
        return float(size), unit

    @property
    def data_zone_value(self):
        size, used_unit = self._size_and_unit()
        allocated_unit = self.unit
        from hs_core.hydroshare.utils import convert_file_size_to_unit
        return convert_file_size_to_unit(size, allocated_unit, used_unit)

    @property
    def unit(self):
        _, unit = self._allocated_value_size_and_unit()
        return unit

    @property
    def used_percent(self):
        try:
            return self.used_value * 100.0 / self.allocated_value
        except ZeroDivisionError:
            return float('inf')

    @property
    def remaining(self):
        delta = self.allocated_value - self.used_value
        return delta if delta > 0 else 0

    @property
    def used_value(self):
        return self.data_zone_value

    def add_to_used_value(self, size):
        """
        return summation of used_value and pass in size in bytes. The returned value
        is in unit specified by self.unit
        :param size: pass in size in bytes unit
        :return: summation of self.used_value and pass in size, converted to the same self.unit
        """
        from hs_core.hydroshare.utils import convert_file_size_to_unit

        return self.used_value + convert_file_size_to_unit(size, self.unit)

    def get_quota_data(self):
        """
        get user quota data for display on user profile page
        :return: dictionary containing quota data

        Note that percents are in the range 0 to 100
        """
        qmsg = QuotaMessage.objects.first()
        if qmsg is None:
            qmsg = QuotaMessage.objects.create()

        soft_limit = qmsg.soft_limit_percent
        allocated = self.allocated_value
        unit = self.unit
        used = self.used_value
        dzp = used * 100.0 / allocated
        percent = used * 100.0 / allocated
        remaining = allocated - used

        status = QuotaStatus.INFO
        if percent >= 100:
            status = QuotaStatus.ENFORCEMENT
        elif percent >= soft_limit:
            status = QuotaStatus.WARNING

        uq_data = {"used": used,
                   "allocated": allocated,
                   "unit": unit,
                   "dz": used,
                   "dz_percent": dzp if dzp < 100 else 100,
                   "percent": percent if percent < 100 else 100,
                   "remaining": 0 if remaining < 0 else remaining,
                   "percent_over": 0 if percent < 100 else percent - 100,
                   "status": status,
                   "qmsg": qmsg,
                   }
        return uq_data

    def get_quota_message(self, quota_data=None, include_quota_usage_info=True):
        """
        get quota warning, grace period, or enforcement message to email users and display
        when the user logins in and display on user profile page
        :param quota_data: dictionary containing quota data
        :return: quota message string
        """
        return_msg = ''
        if not quota_data:
            quota_data = self.get_quota_data()
        qmsg = quota_data["qmsg"]
        allocated = quota_data["allocated"]
        used = quota_data["used"]
        quota_status = quota_data["status"]
        percent = used * 100.0 / allocated
        rounded_percent = round(percent, 2)
        rounded_used_val = round(used, 4)

        if quota_status == QuotaStatus.ENFORCEMENT:
            # return quota enforcement message
            if include_quota_usage_info:
                msg_template_str = f'{qmsg.enforce_content_prepend} {qmsg.quota_usage_info} {qmsg.content}\n'
            else:
                msg_template_str = f'{qmsg.enforce_content_prepend} {qmsg.content}\n'
            return_msg += msg_template_str.format(used=rounded_used_val,
                                                  unit=self.unit,
                                                  allocated=self.allocated_value,
                                                  zone=self.zone,
                                                  percent=rounded_percent)
        elif quota_status == QuotaStatus.WARNING:
            # return quota warning message
            if include_quota_usage_info:
                msg_template_str = f'{qmsg.quota_usage_info} {qmsg.warning_content_prepend} {qmsg.content}\n'
            else:
                msg_template_str = f'{qmsg.warning_content_prepend} {qmsg.content}\n'
            return_msg += msg_template_str.format(used=rounded_used_val,
                                                  unit=self.unit,
                                                  allocated=self.allocated_value,
                                                  zone=self.zone,
                                                  percent=rounded_percent)
        else:
            # return quota informational message
            if include_quota_usage_info:
                msg_template_str = f'{qmsg.quota_usage_info} {qmsg.warning_content_prepend}\n'
            else:
                msg_template_str = f'{qmsg.warning_content_prepend}\n'
            return_msg += msg_template_str.format(allocated=self.allocated_value,
                                                  unit=self.unit,
                                                  used=rounded_used_val,
                                                  zone=self.zone,
                                                  percent=rounded_percent)
        return return_msg


class QuotaRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'pending'),
        ('denied', 'denied'),
        ('approved', 'approved'),
        ('revoked', 'revoked'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ru2qrequest')
    quota = models.ForeignKey(UserQuota, on_delete=models.CASCADE, related_name='g2qrequest')
    date_requested = models.DateTimeField(editable=False, auto_now_add=True)
    justification = models.TextField(validators=[MinLengthValidator(15, 'must contain at least 15 characters'),
                                                 MaxLengthValidator(300, 'maximum 300 characters')], null=True)
    storage = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], default=1)

    def notify_user_of_quota_action(self, send_on_deny=False):
        """
        Sends email notification to user on approval/denial of thie quota request

        :param send_on_deny: whether emails should be sent on denial. default is to only send emails on quota approval
        :return:
        """

        if self.status != 'approved' and not send_on_deny:
            return

        date = self.date_requested.strftime("%m/%d/%Y, %H:%M:%S")
        email_msg = f'''Dear Hydroshare User,
        <p>On {date}, you requested {self.storage} GB increase in quota.</p>
        <p>Here is the justification you provided: <strong>'{self.justification}'</strong></p>

        <p>Your request for Quota increase has been reviewed and {self.status}.</p>

        <p>Thank you,</p>
        <p>The HydroShare Team</p>
        '''
        send_mail(subject=f"HydroShare request for Quota increase {self.status}",
                  message=email_msg,
                  html_message=email_msg,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[self.request_from.email])


class QuotaRequestForm(ModelForm):
    class Meta:
        model = QuotaRequest
        fields = ["justification", "storage"]

    def __init__(self, *args, **kwargs):
        super(QuotaRequestForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = ThumbnailImageField(
        upload_to=get_upload_path_userprofile, null=True, blank=True
    )
    middle_name = models.CharField(max_length=1024, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    title = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="e.g. Assistant Professor, Program Director, Adjunct Professor, Software Developer.",
    )
    user_type = models.CharField(
        max_length=1024, null=True, blank=True, default="Unspecified"
    )
    subject_areas = ArrayField(
        models.CharField(max_length=1024),
        help_text='A list of subject areas you are interested in researching. e.g. "Water Management." '
                  'Free text entry or select from the suggestions',
        null=True, blank=True
    )
    organization = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="The name of the organization you work for.",
    )
    phone_1 = models.CharField(
        max_length=32, null=True, blank=True
    )
    phone_1_type = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        choices=(
            ("Home", "Home"),
            ("Work", "Work"),
            ("Mobile", "Mobile"),
        ),
    )
    phone_2 = models.CharField(
        max_length=32, null=True, blank=True
    )
    phone_2_type = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        choices=(
            ("Home", "Home"),
            ("Work", "Work"),
            ("Mobile", "Mobile"),
        ),
    )
    public = models.BooleanField(
        default=True,
        help_text="Uncheck to make your profile contact information and "
        "details private.",
    )
    cv = models.FileField(
        upload_to="profile",
        help_text="Upload your Curriculum Vitae if you wish people to be able to download it.",
        null=True,
        blank=True,
    )
    details = models.TextField(
        "Description",
        help_text="Tell the HydroShare community a little about yourself.",
        null=True,
        blank=True,
    )

    state = models.CharField(max_length=1024, null=True, blank=True)
    country = models.CharField(max_length=1024, null=True, blank=True)

    # to store one or more external identifier (Google Scholar, ResearchGate, ORCID etc)
    # each identifier is stored as a key/value pair {name:link}
    identifiers = HStoreField(default=dict, null=True, blank=True)

    email_opt_out = models.BooleanField(default=False)

    _bucket_name = models.CharField(max_length=63, null=True, editable=False, unique=True)

    def __init__(self, *args, **kwargs):
        '''We set the _bucket_name during user creation
        However we only create the bucket once the user has a resource
        '''
        super().__init__(*args, **kwargs)
        self._assign_bucket_name()

    def _assign_bucket_name(self):
        '''Assign a bucket name to the user profile
        The bucket name is derived from the user's username
        '''
        safe_username = re.sub(r"[^A-Za-z0-9\.-]", "", self.user.username.lower())
        # limit the length to 60 characters (max length for a bucket name is 63 characters)
        base_safe_username = safe_username[:60].strip()
        safe_username = base_safe_username
        # there is a small chance a bucket name exists for another user with the safe_username transformation
        # in that case, we append a unique number to the bucket name
        id_number = 1
        if len(safe_username) < 3:
            # ensures a minimum character count of 3 for the bucket name
            safe_username = f"{safe_username}-{id_number}"
        while UserProfile.objects.filter(_bucket_name=safe_username).exclude(id=self.id).exists():
            safe_username = f"{base_safe_username}-{id_number}"
            id_number += 1
        self._bucket_name = safe_username

    @property
    def profile_is_missing(self):
        missing = []
        if not self.country:
            missing.append("Country")
        if not self.organization:
            missing.append("Organization")
        if not self.user_type:
            missing.append("User Type")
        return missing

    @property
    def bucket_name(self):
        return self._bucket_name


def force_unique_emails(sender, instance, **kwargs):
    if instance:
        email = instance.email
        username = instance.username

        if not email:
            raise ValidationError("Email required.")
        # check for email use first, it's more helpful to know about than username duplication
        if sender.objects.filter(email=email).exclude(pk=instance.id).count():
            # this string is being checked in base.html to provide reset password link
            raise ValidationError("Email already in use.")
        if sender.objects.filter(username=username).exclude(pk=instance.id).exists():
            raise ValidationError("Username already in use.")


pre_save.connect(force_unique_emails, sender=User)


@receiver(models.signals.pre_save, sender=UserProfile)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem when corresponding UserProfile object is updated with new file.
    instance is a fixed argument name in models.signals.pre_save providing_args signature, so cannot be renamed
    """
    if not instance.pk:
        # if pk is None, it is a new profile instance, no need to check further
        return

    try:
        up = UserProfile.objects.get(pk=instance.pk)
        old_file_cv = up.cv
        old_file_pic = up.picture
        if not old_file_cv and not old_file_pic:
            return
    except UserProfile.DoesNotExist:
        logger.warning(
            f"user profile for {instance.pk} does not exist when trying to update it"
        )
        return

    try:
        updated_profile = instance
        if old_file_cv and old_file_cv != updated_profile.cv:
            old_file_cv.delete()
        if old_file_pic and old_file_pic != updated_profile.picture:
            old_file_pic.delete()
        return
    except Exception as e:
        logger.error(f"Error deleting profile file {old_file_cv}: {e}")


@receiver(models.signals.post_save, sender=QuotaRequest)
def update_user_quota_on_quota_request(sender, instance, **kwargs):
    """
    Increment the allocated_value for a UserQuota object uppon approval of a QuotaRequest
    """
    if kwargs.get('created'):
        # it is a new QuotaRequest instance, no need to check further
        return
    if instance.status != 'approved':
        return

    try:
        qr = QuotaRequest.objects.select_related("quota").get(pk=instance.pk)
        new_storage_amount = qr.storage
        if qr.quota.unit != "GB":
            from hs_core.hydroshare.utils import convert_file_size_to_unit
            new_storage_amount = convert_file_size_to_unit(qr.storage, qr.quota.unit, "GB")
        istorage = S3Storage()
        # If a user hasn't created a resource yet, the bucket won't exist
        if not istorage.bucket_exists(qr.quota.user.userprofile.bucket_name):
            istorage.create_bucket(qr.quota.user.userprofile.bucket_name)
        qr.quota.save_allocated_value(qr.quota.allocated_value + new_storage_amount, qr.quota.unit)

        qr.quota.save()
        qr.notify_user_of_quota_action()
    except QuotaRequest.DoesNotExist:
        logger.warning(
            f"QuotaRequest for {instance.pk} does not exist when trying to update it"
        )
