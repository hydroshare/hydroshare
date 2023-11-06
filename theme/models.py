import datetime
import os
import logging

from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import models
from django.forms import ModelForm
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import pre_save
from django.template import RequestContext, Template, TemplateSyntaxError
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import HStoreField

from mezzanine.core.fields import FileField, RichTextField
from mezzanine.core.models import Orderable, SiteRelated
from mezzanine.core.request import current_request
from mezzanine.pages.models import Page
from mezzanine.utils.models import upload_to

from sorl.thumbnail import ImageField as ThumbnailImageField
from theme.utils import get_upload_path_userprofile


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
    # user and displayed when the user is logged in; grace_period_cotent_prepend prepends the
    # content when over quota within grace period and less than 125% of hard limit quota;
    # enforce_content_prepend prepends the content to form an enforcement message to inform users
    # after grace period or when they are over hard limit quota
    warning_content_prepend = models.TextField(
        default="Your quota for HydroShare resources is "
        "{allocated}{unit} in {zone} zone. You "
        "currently have resources that consume "
        "{used}{unit}, {percent}% of your quota. "
        "Once your quota reaches 100% you will no "
        "longer be able to create new resources in "
        "HydroShare. "
    )
    grace_period_content_prepend = models.TextField(
        default="You have exceeded your HydroShare "
        "quota. Your quota for HydroShare "
        "resources is {allocated}{unit} in "
        "{zone} zone. You currently have "
        "resources that consume {used}{unit}, "
        "{percent}% of your quota. You have a "
        "grace period until {cut_off_date} to "
        "reduce your use to below your quota, "
        "or to acquire additional quota, after "
        "which you will no longer be able to "
        "create new resources in HydroShare. "
    )
    enforce_content_prepend = models.TextField(
        default="Your action "
        "was refused because you have exceeded your "
        "quota. Your quota for HydroShare resources "
        "is {allocated}{unit} in {zone} zone. You "
        "currently have resources that consume "
        "{used}{unit}, {percent}% of your quota. "
    )
    content = models.TextField(
        default="To request additional quota, please contact "
        "help@cuahsi.org. We will try to accommodate "
        "reasonable requests for additional quota. If you have a "
        "large quota request you may need to contribute toward the "
        "costs of providing the additional space you need. See "
        "https://help.hydroshare.org/about-hydroshare/policies/"
        "quota/ for more information about the quota policy."
    )
    # quota soft limit percent value for starting to show quota usage warning. Default is 80%
    soft_limit_percent = models.IntegerField(default=80)
    # quota hard limit percent value for hard quota enforcement. Default is 125%
    hard_limit_percent = models.IntegerField(default=125)
    # TODO: #5228
    # percent that published resources should count toward quota
    # Default=0 -> published resources aren't counted toward quota
    published_resource_percent = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0)
    # grace period, default is 7 days
    grace_period = models.IntegerField(default=7)
    # whether to enforce quota or not. Default is False, which can be changed to true from
    # admin panel when needed
    enforce_quota = models.BooleanField(default=False)


class UserQuota(models.Model):
    # ForeignKey relationship makes it possible to associate multiple UserQuota models to
    # a User with each UserQuota model defining quota for a set of iRODS zones. By default,
    # the UserQuota model instance defines quota in hydroshareZone and hydroshareuserZone,
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

    allocated_value = models.FloatField(default=20)
    used_value = models.FloatField(default=0)
    unit = models.CharField(max_length=10, default="GB")
    zone = models.CharField(max_length=100, default="hydroshare")
    # remaining_grace_period to be quota-enforced. Default is -1 meaning the user is below
    # soft quota limit and thus grace period has not started. When grace period is 0, quota
    # enforcement takes place
    remaining_grace_period = models.IntegerField(default=-1)

    class Meta:
        verbose_name = _("User quota")
        verbose_name_plural = _("User quotas")
        unique_together = ("user", "zone")

    @property
    def used_percent(self):
        return self.used_value * 100.0 / self.allocated_value

    def update_used_value(self, size):
        """
        set self.used_value in self.unit with pass in size in bytes.
        :param size: pass in size in bytes unit
        :return:
        """
        from hs_core.hydroshare.utils import convert_file_size_to_unit

        self.used_value = convert_file_size_to_unit(size, self.unit)
        self.save()

    def add_to_used_value(self, size):
        """
        return summation of used_value and pass in size in bytes. The returned value
        is in unit specified by self.unit
        :param size: pass in size in bytes unit
        :return: summation of self.used_value and pass in size, converted to the same self.unit
        """
        from hs_core.hydroshare.utils import convert_file_size_to_unit

        return self.used_value + convert_file_size_to_unit(size, self.unit)


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
    justification = models.TextField(null=True, blank=True, max_length=300)
    storage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)


class QuotaRequestForm(ModelForm):
    class Meta:
        model = QuotaRequest
        fields = ["justification", "storage"]
        labels = {
            "justification": _("Enter justification for more quota"),
            "storage": _("How much more storage to you require? (GB)"),
        }

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

    create_irods_user_account = models.BooleanField(
        default=False,
        help_text="Check to create an iRODS user account in HydroShare user "
        "iRODS space for staging large files (>2GB) using iRODS clients such as Cyberduck "
        "(https://cyberduck.io/) and icommands (https://docs.irods.org/master/icommands/user/)."
        "Uncheck to delete your iRODS user account. Note that deletion of your iRODS user "
        "account deletes all of your files under this account as well.",
    )

    # to store one or more external identifier (Google Scholar, ResearchGate, ORCID etc)
    # each identifier is stored as a key/value pair {name:link}
    identifiers = HStoreField(default=dict, null=True, blank=True)

    email_opt_out = models.BooleanField(default=False)


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

    updated_profile = instance
    if old_file_cv and old_file_cv != updated_profile.cv:
        if os.path.isfile(old_file_cv.path):
            os.remove(old_file_cv.path)
    if old_file_pic and old_file_pic != updated_profile.picture:
        if os.path.isfile(old_file_pic.path):
            os.remove(old_file_pic.path)
    return
