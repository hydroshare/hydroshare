from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.template import RequestContext, Template, TemplateSyntaxError
from django.utils.translation import ugettext_lazy as _

from mezzanine.core.fields import FileField, RichTextField
from mezzanine.core.models import Orderable, SiteRelated
from mezzanine.core.request import current_request
from mezzanine.pages.models import Page
from mezzanine.utils.models import upload_to

class UserProfile(models.Model):

    UNIVERSITY_FACULTY = 1
    UNIVERSITY_PROFESSIONAL_OR_RESEARCH_STAFF = 2
    POST_DOCTORAL_FELLOW = 3
    UNIVERSITY_GRADUATE_STUDENT = 4
    UNIVERSITY_UNDERGRADUATE_STUDENT = 5
    COMMERCIAL_OR_PROFESSIONAL = 6
    GOVERNMENT_OFFICIAL = 7
    SCHOOL_STUDENT_K_TO_12 = 8
    SCHOOL_TEACHER_K_TO_12 = 9
    OTHER = 10

    USER_TYPE_CHOICES = (
        (UNIVERSITY_FACULTY, 'University Faculty'),
        (UNIVERSITY_PROFESSIONAL_OR_RESEARCH_STAFF, 'University Professional or Research Staff'),
        (POST_DOCTORAL_FELLOW, 'Post Doctoral Fellow'),
        (UNIVERSITY_GRADUATE_STUDENT, 'University Graduate Student'),
        (UNIVERSITY_UNDERGRADUATE_STUDENT, 'University Undergraduate Student'),
        (COMMERCIAL_OR_PROFESSIONAL, 'Commercial or Professional'),
        (GOVERNMENT_OFFICIAL, 'Government Official'),
        (SCHOOL_STUDENT_K_TO_12, 'School Student Kindergarten to 12th Grade'),
        (SCHOOL_TEACHER_K_TO_12, 'School Teacher Kindergarten to 12th Grade'),
        (OTHER, 'Other'),
    )

    user = models.OneToOneField(User)
    picture = models.ImageField(upload_to='profile', null=True, blank=True)

    title = models.CharField(
        max_length=1024, null=True, blank=True,
        help_text='e.g. Assistant Professor, Program Director, Adjunct Professor, Software Developer.')
    profession = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        default='Student',
        help_text='e.g. Student, Researcher, Research Faculty, Research Staff, Project Manager, Teacher, Research Assistant.'
    )
    subject_areas = models.CharField(
        max_length=1024, null=True, blank=True,
        help_text='A comma-separated list of subject areas you are interested in researching. e.g. "Computer Science, Hydrology, Water Management"')
    organization = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="The name of the organization you work for."
    )
    organization_type = models.CharField(max_length=1024, null=True, blank=True, choices=(
        ('Higher Education','Higher Education'),
        ('Research','Research'),
        ('Government','Government'),
        ('Commercial','Commercial'),
        ('Primary Education','Primary Education'),
        ('Secondary Education', 'Secondary Education'),
    ))
    phone_1 = models.CharField(max_length=1024, null=True, blank=True)
    phone_1_type = models.CharField(max_length=1024, null=True, blank=True, choices=(
        ('Home','Home'),
        ('Work','Work'),
        ('Mobile','Mobile'),
    ))
    phone_2 = models.CharField(max_length=1024, null=True, blank=True)
    phone_2_type = models.CharField(max_length=1024, null=True, blank=True, choices=(
        ('Home','Home'),
        ('Work','Work'),
        ('Mobile','Mobile'),
    ))
    public = models.BooleanField(default=True, help_text='Uncheck to make your profile contact information and details private.')
    cv = models.FileField(upload_to='profile', help_text='Upload your Curriculum Vitae if you wish people to be able to download it.', null=True, blank=True)
    details = models.TextField("Description", help_text='Tell the HydroShare community a little about yourself.', null=True, blank=True)

    # middle_name = models.CharField(max_length=100, null=True)
    # homepage = models.URLField(null=True)
    # user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=OTHER)
    # user_type_other = models.CharField(max_length=100, null=False)

    class Meta:
        db_table = "theme_userprofile"

    def __unicode__(self):
        return "{0} ({1})".format(user.username, self.user_type)

def create_user_profile(sender, instance, created, **kwargs):
   if created:
      UserProfile.objects.get_or_create(user=user)

create_profile_on_save = post_save.connect(User, create_user_profile, weak=False)


class Organization(models.Model):
    """
    University, company, non-profit, or other similar entity that creates, shares, or consumes
    hydrology data.
    """
    ANALYTICAL_LABORATORY = 1
    ASSOCIATION = 2
    CENTER = 3
    COLLEGE = 4
    COMPANY = 5
    CONSORTIUM = 6
    DEPARTMENT = 7
    DIVISION = 8
    FOUNDATION = 9
    FUNDING_ORGANIZATION = 10
    GOVERNMENT_AGENCY = 11
    INSTITUTE = 12
    LABORATORY = 13
    LIBRARY = 14
    MANUFACTURER = 15
    MUSEUM = 16
    PROGRAM = 17
    PUBLISHER = 18
    RESEARCH_AGENCY = 19
    RESEARCH_INSTITUTE = 20
    RESEARCH_ORGANIZATION = 21
    SCHOOL = 22
    STUDENT_ORGANIZATION = 23
    UNIVERSITY = 24
    UNKNOWN = 25
    VENDOR = 26
    OTHER = 27

    ORG_TYPE_CHOICES = (
       (ANALYTICAL_LABORATORY, 'Analytical laboratory'),
       (ASSOCIATION, 'Association'),
       (CENTER , 'Center'),
       (COLLEGE, 'College'),
       (COMPANY, 'Company'),
       (CONSORTIUM, 'Consortium'),
       (DEPARTMENT, 'Department'),
       (DIVISION, 'Division'),
       (FOUNDATION, 'Foundation'),
       (FUNDING_ORGANIZATION, 'Funding organization'),
       (GOVERNMENT_AGENCY, 'Government agency'),
       (INSTITUTE, 'Institute'),
       (LABORATORY, 'Laboratory'),
       (LIBRARY, 'Library'),
       (MANUFACTURER, 'Manufacturer'),
       (MUSEUM, 'Museum'),
       (PROGRAM, 'Program'),
       (PUBLISHER, 'Publisher'),
       (RESEARCH_AGENCY, 'Research agency'),
       (RESEARCH_INSTITUTE, 'Research institute'),
       (RESEARCH_ORGANIZATION, 'Research organization'),
       (SCHOOL, 'School'),
       (STUDENT_ORGANIZATION, 'Student organization'),
       (UNIVERSITY, 'University'),
       (UNKNOWN, 'Unknown'),
       (VENDOR, 'Vendor'),
       (OTHER, 'Other'),
    )

    org_type = models.IntegerField(choices=ORG_TYPE_CHOICES, default=UNKNOWN)
    org_type_other = models.CharField(max_length=100, null=False)
    name = models.CharField(max_length=100, null=False)
    code = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=255, null=True)
    homepage = models.URLField(null=True)
    # TODO: add logo field

    def __unicode__(self):
        return "{0}: {1}".format(self.code, self.name)


class Affiliation(models.Model):
    """
    Annotated relationship between a Person and and Organization with job title, department, and
    active date information.
    """
    organization = models.ForeignKey(Organization)
    person = models.ForeignKey(UserProfile)
    job_title = models.CharField(max_length=100, null=True)
    department_name = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=250, null=True)
    phone = models.CharField(max_length=25, null=True)
    date_begin = models.DateField(null=True)
    date_end = models.DateField(null=True)
    phone = models.CharField(max_length=25, null=True)

    def __unicode__(self):
        return "{0} {1} ({2} at {3})".format(person.first_name,
                                             person.last_name,
                                             self.job_title,
                                             organization.name)


class ExternalProfileLink(models.Model):
    profile_type = models.CharField(max_length=50) # this used to be type, a reserved keyword
    url = models.URLField()
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ("type", "url", "object_id")
