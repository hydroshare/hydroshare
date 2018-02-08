# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_irods.storage
import django.utils.timezone
from django.conf import settings
import hs_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('pages', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bags',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('description', models.URLField(blank=True, null=True, validators=[hs_core.models.validate_user_url])),
                ('name', models.CharField(max_length=100)),
                ('organization', models.CharField(max_length=200, null=True, blank=True)),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
                ('address', models.CharField(max_length=250, null=True, blank=True)),
                ('phone', models.CharField(max_length=25, null=True, blank=True)),
                ('homepage', models.URLField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_core_contributor_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CoreMetaData',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Coverage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('type', models.CharField(max_length=20, choices=[(b'box', b'Box'), (b'point', b'Point'), (b'period', b'Period')])),
                ('_value', models.CharField(max_length=1024)),
                ('content_type', models.ForeignKey(related_name='hs_core_coverage_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Creator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('description', models.URLField(blank=True, null=True, validators=[hs_core.models.validate_user_url])),
                ('name', models.CharField(max_length=100)),
                ('organization', models.CharField(max_length=200, null=True, blank=True)),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
                ('address', models.CharField(max_length=250, null=True, blank=True)),
                ('phone', models.CharField(max_length=25, null=True, blank=True)),
                ('homepage', models.URLField(null=True, blank=True)),
                ('order', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='hs_core_creator_related', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Date',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('type', models.CharField(max_length=20, choices=[(b'created', b'Created'), (b'modified', b'Modified'), (b'valid', b'Valid'), (b'available', b'Available'), (b'published', b'Published')])),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_core_date_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Description',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('abstract', models.TextField()),
                ('content_type', models.ForeignKey(related_name='hs_core_description_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExternalProfileLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=50)),
                ('url', models.URLField()),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Format',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=150)),
                ('content_type', models.ForeignKey(related_name='hs_core_format_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GenericResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='pages.Page')),
                ('comments_count', models.IntegerField(default=0, editable=False)),
                ('rating_count', models.IntegerField(default=0, editable=False)),
                ('rating_sum', models.IntegerField(default=0, editable=False)),
                ('rating_average', models.FloatField(default=0, editable=False)),
                ('public', models.BooleanField(default=True, help_text=b'If this is true, the resource is viewable and downloadable by anyone')),
                ('frozen', models.BooleanField(default=False, help_text=b'If this is true, the resource should not be modified')),
                ('do_not_distribute', models.BooleanField(default=False, help_text=b'If this is true, the resource owner has to designate viewers')),
                ('discoverable', models.BooleanField(default=True, help_text=b'If this is true, it will turn up in searches.')),
                ('published_and_frozen', models.BooleanField(default=False, help_text=b'Once this is true, no changes can be made to the resource')),
                ('content', models.TextField()),
                ('short_id', models.CharField(default=hs_core.models.short_id, max_length=32, db_index=True)),
                ('doi', models.CharField(help_text=b"Permanent identifier. Never changes once it's been set.", max_length=1024, null=True, db_index=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_hs_core_genericresource', to=settings.AUTH_USER_MODEL, help_text=b'This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text=b'This is the set of CommonsShare Groups who can edit the resource', related_name='group_editable_hs_core_genericresource', null=True, to=b'auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text=b'This is the set of CommonsShare Users who can edit the resource', related_name='user_editable_hs_core_genericresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_core_genericresource', to=settings.AUTH_USER_MODEL, help_text=b'The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text=b'The person who has total ownership of the resource', related_name='owns_hs_core_genericresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='genericresources', verbose_name='Author', to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text=b'This is the set of CommonsShare Groups who can view the resource', related_name='group_viewable_hs_core_genericresource', null=True, to=b'auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text=b'This is the set of CommonsShare Users who can view the resource', related_name='user_viewable_hs_core_genericresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'Generic',
            },
            bases=('pages.page', models.Model),
        ),
        migrations.CreateModel(
            name='GroupOwnership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='auth.Group')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField(unique=True)),
                ('content_type', models.ForeignKey(related_name='hs_core_identifier_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('code', models.CharField(max_length=3, choices=[(b'aar', b'Afar'), (b'abk', b'Abkhazian'), (b'ace', b'Achinese'), (b'ach', b'Acoli'), (b'ada', b'Adangme'), (b'ady', b'Adyghe; Adygei'), (b'afa', b'Afro-Asiatic languages'), (b'afh', b'Afrihili'), (b'afr', b'Afrikaans'), (b'ain', b'Ainu'), (b'aka', b'Akan'), (b'akk', b'Akkadian'), (b'alb', b'Albanian'), (b'ale', b'Aleut'), (b'alg', b'Algonquian languages'), (b'alt', b'Southern Altai'), (b'amh', b'Amharic'), (b'ang', b'English, Old (ca.450-1100)'), (b'anp', b'Angika'), (b'apa', b'Apache languages'), (b'ara', b'Arabic'), (b'arc', b'Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)'), (b'arg', b'Aragonese'), (b'arm', b'Armenian'), (b'arn', b'Mapudungun; Mapuche'), (b'arp', b'Arapaho'), (b'art', b'Artificial languages'), (b'arw', b'Arawak'), (b'asm', b'Assamese'), (b'ast', b'Asturian; Bable; Leonese; Asturleonese'), (b'ath', b'Athapascan languages'), (b'aus', b'Australian languages'), (b'ava', b'Avaric'), (b'ave', b'Avestan'), (b'awa', b'Awadhi'), (b'aym', b'Aymara'), (b'aze', b'Azerbaijani'), (b'bad', b'Banda languages'), (b'bai', b'Bamileke languages'), (b'bak', b'Bashkir'), (b'bal', b'Baluchi'), (b'bam', b'Bambara'), (b'ban', b'Balinese'), (b'baq', b'Basque'), (b'bas', b'Basa'), (b'bat', b'Baltic languages'), (b'bej', b'Beja; Bedawiyet'), (b'bel', b'Belarusian'), (b'bem', b'Bemba'), (b'ben', b'Bengali'), (b'ber', b'Berber languages'), (b'bho', b'Bhojpuri'), (b'bih', b'Bihari languages'), (b'bik', b'Bikol'), (b'bin', b'Bini; Edo'), (b'bis', b'Bislama'), (b'bla', b'Siksika'), (b'bnt', b'Bantu languages'), (b'tib', b'Tibetan'), (b'bos', b'Bosnian'), (b'bra', b'Braj'), (b'bre', b'Breton'), (b'btk', b'Batak languages'), (b'bua', b'Buriat'), (b'bug', b'Buginese'), (b'bul', b'Bulgarian'), (b'bur', b'Burmese'), (b'byn', b'Blin; Bilin'), (b'cad', b'Caddo'), (b'cai', b'Central American Indian languages'), (b'car', b'Galibi Carib'), (b'cat', b'Catalan; Valencian'), (b'cau', b'Caucasian languages'), (b'ceb', b'Cebuano'), (b'cel', b'Celtic languages'), (b'cze', b'Czech'), (b'cha', b'Chamorro'), (b'chb', b'Chibcha'), (b'che', b'Chechen'), (b'chg', b'Chagatai'), (b'chi', b'Chinese'), (b'chk', b'Chuukese'), (b'chm', b'Mari'), (b'chn', b'Chinook jargon'), (b'cho', b'Choctaw'), (b'chp', b'Chipewyan; Dene Suline'), (b'chr', b'Cherokee'), (b'chu', b'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'), (b'chv', b'Chuvash'), (b'chy', b'Cheyenne'), (b'cmc', b'Chamic languages'), (b'cop', b'Coptic'), (b'cor', b'Cornish'), (b'cos', b'Corsican'), (b'cpe', b'Creoles and pidgins, English based'), (b'cpf', b'Creoles and pidgins, French-based'), (b'cpp', b'Creoles and pidgins, Portuguese-based'), (b'cre', b'Cree'), (b'crh', b'Crimean Tatar; Crimean Turkish'), (b'crp', b'Creoles and pidgins'), (b'csb', b'Kashubian'), (b'cus', b'Cushitic languages'), (b'wel', b'Welsh'), (b'dak', b'Dakota'), (b'dan', b'Danish'), (b'dar', b'Dargwa'), (b'day', b'Land Dayak languages'), (b'del', b'Delaware'), (b'den', b'Slave (Athapascan)'), (b'ger', b'German'), (b'dgr', b'Dogrib'), (b'din', b'Dinka'), (b'div', b'Divehi; Dhivehi; Maldivian'), (b'doi', b'Dogri'), (b'dra', b'Dravidian languages'), (b'dsb', b'Lower Sorbian'), (b'dua', b'Duala'), (b'dum', b'Dutch, Middle (ca.1050-1350)'), (b'dut', b'Dutch; Flemish'), (b'dyu', b'Dyula'), (b'dzo', b'Dzongkha'), (b'efi', b'Efik'), (b'egy', b'Egyptian (Ancient)'), (b'eka', b'Ekajuk'), (b'gre', b'Greek, Modern (1453-)'), (b'elx', b'Elamite'), (b'eng', b'English'), (b'enm', b'English, Middle (1100-1500)'), (b'epo', b'Esperanto'), (b'est', b'Estonian'), (b'ewe', b'Ewe'), (b'ewo', b'Ewondo'), (b'fan', b'Fang'), (b'fao', b'Faroese'), (b'per', b'Persian'), (b'fat', b'Fanti'), (b'fij', b'Fijian'), (b'fil', b'Filipino; Pilipino'), (b'fin', b'Finnish'), (b'fiu', b'Finno-Ugrian languages'), (b'fon', b'Fon'), (b'fre', b'French'), (b'frm', b'French, Middle (ca.1400-1600)'), (b'fro', b'French, Old (842-ca.1400)'), (b'frr', b'Northern Frisian'), (b'frs', b'Eastern Frisian'), (b'fry', b'Western Frisian'), (b'ful', b'Fulah'), (b'fur', b'Friulian'), (b'gaa', b'Ga'), (b'gay', b'Gayo'), (b'gba', b'Gbaya'), (b'gem', b'Germanic languages'), (b'geo', b'Georgian'), (b'gez', b'Geez'), (b'gil', b'Gilbertese'), (b'gla', b'Gaelic; Scottish Gaelic'), (b'gle', b'Irish'), (b'glg', b'Galician'), (b'glv', b'Manx'), (b'gmh', b'German, Middle High (ca.1050-1500)'), (b'goh', b'German, Old High (ca.750-1050)'), (b'gon', b'Gondi'), (b'gor', b'Gorontalo'), (b'got', b'Gothic'), (b'grb', b'Grebo'), (b'grc', b'Greek, Ancient (to 1453)'), (b'grn', b'Guarani'), (b'gsw', b'Swiss German; Alemannic; Alsatian'), (b'guj', b'Gujarati'), (b'gwi', b"Gwich'in"), (b'hai', b'Haida'), (b'hat', b'Haitian; Haitian Creole'), (b'hau', b'Hausa'), (b'haw', b'Hawaiian'), (b'heb', b'Hebrew'), (b'her', b'Herero'), (b'hil', b'Hiligaynon'), (b'him', b'Himachali languages; Western Pahari languages'), (b'hin', b'Hindi'), (b'hit', b'Hittite'), (b'hmn', b'Hmong; Mong'), (b'hmo', b'Hiri Motu'), (b'hrv', b'Croatian'), (b'hsb', b'Upper Sorbian'), (b'hun', b'Hungarian'), (b'hup', b'Hupa'), (b'iba', b'Iban'), (b'ibo', b'Igbo'), (b'ice', b'Icelandic'), (b'ido', b'Ido'), (b'iii', b'Sichuan Yi; Nuosu'), (b'ijo', b'Ijo languages'), (b'iku', b'Inuktitut'), (b'ile', b'Interlingue; Occidental'), (b'ilo', b'Iloko'), (b'ina', b'Interlingua (International Auxiliary Language Association)'), (b'inc', b'Indic languages'), (b'ind', b'Indonesian'), (b'ine', b'Indo-European languages'), (b'inh', b'Ingush'), (b'ipk', b'Inupiaq'), (b'ira', b'Iranian languages'), (b'iro', b'Iroquoian languages'), (b'ita', b'Italian'), (b'jav', b'Javanese'), (b'jbo', b'Lojban'), (b'jpn', b'Japanese'), (b'jpr', b'Judeo-Persian'), (b'jrb', b'Judeo-Arabic'), (b'kaa', b'Kara-Kalpak'), (b'kab', b'Kabyle'), (b'kac', b'Kachin; Jingpho'), (b'kal', b'Kalaallisut; Greenlandic'), (b'kam', b'Kamba'), (b'kan', b'Kannada'), (b'kar', b'Karen languages'), (b'kas', b'Kashmiri'), (b'kau', b'Kanuri'), (b'kaw', b'Kawi'), (b'kaz', b'Kazakh'), (b'kbd', b'Kabardian'), (b'kha', b'Khasi'), (b'khi', b'Khoisan languages'), (b'khm', b'Central Khmer'), (b'kho', b'Khotanese; Sakan'), (b'kik', b'Kikuyu; Gikuyu'), (b'kin', b'Kinyarwanda'), (b'kir', b'Kirghiz; Kyrgyz'), (b'kmb', b'Kimbundu'), (b'kok', b'Konkani'), (b'kom', b'Komi'), (b'kon', b'Kongo'), (b'kor', b'Korean'), (b'kos', b'Kosraean'), (b'kpe', b'Kpelle'), (b'krc', b'Karachay-Balkar'), (b'krl', b'Karelian'), (b'kro', b'Kru languages'), (b'kru', b'Kurukh'), (b'kua', b'Kuanyama; Kwanyama'), (b'kum', b'Kumyk'), (b'kur', b'Kurdish'), (b'kut', b'Kutenai'), (b'lad', b'Ladino'), (b'lah', b'Lahnda'), (b'lam', b'Lamba'), (b'lao', b'Lao'), (b'lat', b'Latin'), (b'lav', b'Latvian'), (b'lez', b'Lezghian'), (b'lim', b'Limburgan; Limburger; Limburgish'), (b'lin', b'Lingala'), (b'lit', b'Lithuanian'), (b'lol', b'Mongo'), (b'loz', b'Lozi'), (b'ltz', b'Luxembourgish; Letzeburgesch'), (b'lua', b'Luba-Lulua'), (b'lub', b'Luba-Katanga'), (b'lug', b'Ganda'), (b'lui', b'Luiseno'), (b'lun', b'Lunda'), (b'luo', b'Luo (Kenya and Tanzania)'), (b'lus', b'Lushai'), (b'mac', b'Macedonian'), (b'mad', b'Madurese'), (b'mag', b'Magahi'), (b'mah', b'Marshallese'), (b'mai', b'Maithili'), (b'mak', b'Makasar'), (b'mal', b'Malayalam'), (b'man', b'Mandingo'), (b'mao', b'Maori'), (b'map', b'Austronesian languages'), (b'mar', b'Marathi'), (b'mas', b'Masai'), (b'may', b'Malay'), (b'mdf', b'Moksha'), (b'mdr', b'Mandar'), (b'men', b'Mende'), (b'mga', b'Irish, Middle (900-1200)'), (b'mic', b"Mi'kmaq; Micmac"), (b'min', b'Minangkabau'), (b'mis', b'Uncoded languages'), (b'mkh', b'Mon-Khmer languages'), (b'mlg', b'Malagasy'), (b'mlt', b'Maltese'), (b'mnc', b'Manchu'), (b'mni', b'Manipuri'), (b'mno', b'Manobo languages'), (b'moh', b'Mohawk'), (b'mon', b'Mongolian'), (b'mos', b'Mossi'), (b'mul', b'Multiple languages'), (b'mun', b'Munda languages'), (b'mus', b'Creek'), (b'mwl', b'Mirandese'), (b'mwr', b'Marwari'), (b'myn', b'Mayan languages'), (b'myv', b'Erzya'), (b'nah', b'Nahuatl languages'), (b'nai', b'North American Indian languages'), (b'nap', b'Neapolitan'), (b'nau', b'Nauru'), (b'nav', b'Navajo; Navaho'), (b'nbl', b'Ndebele, South; South Ndebele'), (b'nde', b'Ndebele, North; North Ndebele'), (b'ndo', b'Ndonga'), (b'nds', b'Low German; Low Saxon; German, Low; Saxon, Low'), (b'nep', b'Nepali'), (b'new', b'Nepal Bhasa; Newari'), (b'nia', b'Nias'), (b'nic', b'Niger-Kordofanian languages'), (b'niu', b'Niuean'), (b'nno', b'Norwegian Nynorsk; Nynorsk, Norwegian'), (b'nob', b'Bokmal, Norwegian; Norwegian Bokmal'), (b'nog', b'Nogai'), (b'non', b'Norse, Old'), (b'nor', b'Norwegian'), (b'nqo', b"N'Ko"), (b'nso', b'Pedi; Sepedi; Northern Sotho'), (b'nub', b'Nubian languages'), (b'nwc', b'Classical Newari; Old Newari; Classical Nepal Bhasa'), (b'nya', b'Chichewa; Chewa; Nyanja'), (b'nym', b'Nyamwezi'), (b'nyn', b'Nyankole'), (b'nyo', b'Nyoro'), (b'nzi', b'Nzima'), (b'oci', b'Occitan (post 1500)'), (b'oji', b'Ojibwa'), (b'ori', b'Oriya'), (b'orm', b'Oromo'), (b'osa', b'Osage'), (b'oss', b'Ossetian; Ossetic'), (b'ota', b'Turkish, Ottoman (1500-1928)'), (b'oto', b'Otomian languages'), (b'paa', b'Papuan languages'), (b'pag', b'Pangasinan'), (b'pal', b'Pahlavi'), (b'pam', b'Pampanga; Kapampangan'), (b'pan', b'Panjabi; Punjabi'), (b'pap', b'Papiamento'), (b'pau', b'Palauan'), (b'peo', b'Persian, Old (ca.600-400 B.C.)'), (b'phi', b'Philippine languages'), (b'phn', b'Phoenician'), (b'pli', b'Pali'), (b'pol', b'Polish'), (b'pon', b'Pohnpeian'), (b'por', b'Portuguese'), (b'pra', b'Prakrit languages'), (b'pro', b'Provencal, Old (to 1500);Occitan, Old (to 1500)'), (b'pus', b'Pushto; Pashto'), (b'qaa-qtz', b'Reserved for local use'), (b'que', b'Quechua'), (b'raj', b'Rajasthani'), (b'rap', b'Rapanui'), (b'rar', b'Rarotongan; Cook Islands Maori'), (b'roa', b'Romance languages'), (b'roh', b'Romansh'), (b'rom', b'Romany'), (b'rum', b'Romanian; Moldavian; Moldovan'), (b'run', b'Rundi'), (b'rup', b'Aromanian; Arumanian; Macedo-Romanian'), (b'rus', b'Russian'), (b'sad', b'Sandawe'), (b'sag', b'Sango'), (b'sah', b'Yakut'), (b'sai', b'South American Indian languages'), (b'sal', b'Salishan languages'), (b'sam', b'Samaritan Aramaic'), (b'san', b'Sanskrit'), (b'sas', b'Sasak'), (b'sat', b'Santali'), (b'scn', b'Sicilian'), (b'sco', b'Scots'), (b'sel', b'Selkup'), (b'sem', b'Semitic languages'), (b'sga', b'Irish, Old (to 900)'), (b'sgn', b'Sign Languages'), (b'shn', b'Shan'), (b'sid', b'Sidamo'), (b'sin', b'Sinhala; Sinhalese'), (b'sio', b'Siouan languages'), (b'sit', b'Sino-Tibetan languages'), (b'sla', b'Slavic languages'), (b'slo', b'Slovak'), (b'slv', b'Slovenian'), (b'sma', b'Southern Sami'), (b'sme', b'Northern Sami'), (b'smi', b'Sami languages'), (b'smj', b'Lule Sami'), (b'smn', b'Inari Sami'), (b'smo', b'Samoan'), (b'sms', b'Skolt Sami'), (b'sna', b'Shona'), (b'snd', b'Sindhi'), (b'snk', b'Soninke'), (b'sog', b'Sogdian'), (b'som', b'Somali'), (b'son', b'Songhai languages'), (b'sot', b'Sotho, Southern'), (b'spa', b'Spanish; Castilian'), (b'srd', b'Sardinian'), (b'srn', b'Sranan Tongo'), (b'srp', b'Serbian'), (b'srr', b'Serer'), (b'ssa', b'Nilo-Saharan languages'), (b'ssw', b'Swati'), (b'suk', b'Sukuma'), (b'sun', b'Sundanese'), (b'sus', b'Susu'), (b'sux', b'Sumerian'), (b'swa', b'Swahili'), (b'swe', b'Swedish'), (b'syc', b'Classical Syriac'), (b'syr', b'Syriac'), (b'tah', b'Tahitian'), (b'tai', b'Tai languages'), (b'tam', b'Tamil'), (b'tat', b'Tatar'), (b'tel', b'Telugu'), (b'tem', b'Timne'), (b'ter', b'Tereno'), (b'tet', b'Tetum'), (b'tgk', b'Tajik'), (b'tgl', b'Tagalog'), (b'tha', b'Thai'), (b'tig', b'Tigre'), (b'tir', b'Tigrinya'), (b'tiv', b'Tiv'), (b'tkl', b'Tokelau'), (b'tlh', b'Klingon; tlhIngan-Hol'), (b'tli', b'Tlingit'), (b'tmh', b'Tamashek'), (b'tog', b'Tonga (Nyasa)'), (b'ton', b'Tonga (Tonga Islands)'), (b'tpi', b'Tok Pisin'), (b'tsi', b'Tsimshian'), (b'tsn', b'Tswana'), (b'tso', b'Tsonga'), (b'tuk', b'Turkmen'), (b'tum', b'Tumbuka'), (b'tup', b'Tupi languages'), (b'tur', b'Turkish'), (b'tut', b'Altaic languages'), (b'tvl', b'Tuvalu'), (b'twi', b'Twi'), (b'tyv', b'Tuvinian'), (b'udm', b'Udmurt'), (b'uga', b'Ugaritic'), (b'uig', b'Uighur; Uyghur'), (b'ukr', b'Ukrainian'), (b'umb', b'Umbundu'), (b'und', b'Undetermined'), (b'urd', b'Urdu'), (b'uzb', b'Uzbek'), (b'vai', b'Vai'), (b'ven', b'Venda'), (b'vie', b'Vietnamese'), (b'vol', b'Volapuk'), (b'vot', b'Votic'), (b'wak', b'Wakashan languages'), (b'wal', b'Wolaitta; Wolaytta'), (b'war', b'Waray'), (b'was', b'Washo'), (b'wen', b'Sorbian languages'), (b'wln', b'Walloon'), (b'wol', b'Wolof'), (b'xal', b'Kalmyk; Oirat'), (b'xho', b'Xhosa'), (b'yao', b'Yao'), (b'yap', b'Yapese'), (b'yid', b'Yiddish'), (b'yor', b'Yoruba'), (b'ypk', b'Yupik languages'), (b'zap', b'Zapotec'), (b'zbl', b'Blissymbols; Blissymbolics; Bliss'), (b'zen', b'Zenaga'), (b'zgh', b'Standard Moroccan Tamazight'), (b'zha', b'Zhuang; Chuang'), (b'znd', b'Zande languages'), (b'zul', b'Zulu'), (b'zun', b'Zuni'), (b'zxx', b'No linguistic content; Not applicable'), (b'zza', b'Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki')])),
                ('content_type', models.ForeignKey(related_name='hs_core_language_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField()),
                ('content_type', models.ForeignKey(related_name='hs_core_publisher_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Relation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('type', models.CharField(max_length=100, choices=[(b'isPartOf', b'Part Of'), (b'isExecutedBy', b'Executed By'), (b'isCreatedBy', b'Created By'), (b'isVersionOf', b'Version Of'), (b'isDataFor', b'Data For'), (b'cites', b'Cites')])),
                ('value', models.CharField(max_length=500)),
                ('content_type', models.ForeignKey(related_name='hs_core_relation_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('resource_file', models.FileField(storage=django_irods.storage.IrodsStorage(), max_length=500, upload_to=hs_core.models.get_path)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Rights',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('statement', models.TextField(null=True, blank=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_core_rights_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('derived_from', models.CharField(max_length=300)),
                ('content_type', models.ForeignKey(related_name='hs_core_source_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=100)),
                ('content_type', models.ForeignKey(related_name='hs_core_subject_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('value', models.CharField(max_length=300)),
                ('content_type', models.ForeignKey(related_name='hs_core_title_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('url', models.URLField()),
                ('content_type', models.ForeignKey(related_name='hs_core_type_related', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='type',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='title',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='rights',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='publisher',
            unique_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='externalprofilelink',
            unique_together=set([('type', 'url', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='description',
            unique_together=set([('content_type', 'object_id')]),
        ),
    ]
