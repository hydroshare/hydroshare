# -*- coding: utf-8 -*-


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
                ('content_type', models.ForeignKey(on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_contributor_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('type', models.CharField(max_length=20, choices=[('box', 'Box'), ('point', 'Point'), ('period', 'Period')])),
                ('_value', models.CharField(max_length=1024)),
                ('content_type', models.ForeignKey(related_name='hs_core_coverage_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_creator_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('type', models.CharField(max_length=20, choices=[('created', 'Created'), ('modified', 'Modified'), ('valid', 'Valid'), ('available', 'Available'), ('published', 'Published')])),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(null=True, blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_core_date_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_description_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_format_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GenericResource',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, on_delete=models.CASCADE, to='pages.Page')),
                ('comments_count', models.IntegerField(default=0, editable=False)),
                ('rating_count', models.IntegerField(default=0, editable=False)),
                ('rating_sum', models.IntegerField(default=0, editable=False)),
                ('rating_average', models.FloatField(default=0, editable=False)),
                ('public', models.BooleanField(default=True, help_text='If this is true, the resource is viewable and downloadable by anyone')),
                ('frozen', models.BooleanField(default=False, help_text='If this is true, the resource should not be modified')),
                ('do_not_distribute', models.BooleanField(default=False, help_text='If this is true, the resource owner has to designate viewers')),
                ('discoverable', models.BooleanField(default=True, help_text='If this is true, it will turn up in searches.')),
                ('published_and_frozen', models.BooleanField(default=False, help_text='Once this is true, no changes can be made to the resource')),
                ('content', models.TextField()),
                ('short_id', models.CharField(default=hs_core.models.short_id, max_length=32, db_index=True)),
                ('doi', models.CharField(help_text=b"Permanent identifier. Never changes once it's been set.", max_length=1024, null=True, db_index=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, on_delete=models.CASCADE, to='contenttypes.ContentType', null=True)),
                ('creator', models.ForeignKey(related_name='creator_of_hs_core_genericresource', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='This is the person who first uploaded the resource')),
                ('edit_groups', models.ManyToManyField(help_text='This is the set of Hydroshare Groups who can edit the resource', related_name='group_editable_hs_core_genericresource', null=True, to='auth.Group', blank=True)),
                ('edit_users', models.ManyToManyField(help_text='This is the set of Hydroshare Users who can edit the resource', related_name='user_editable_hs_core_genericresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('last_changed_by', models.ForeignKey(related_name='last_changed_hs_core_genericresource', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL, help_text='The person who last changed the resource', null=True)),
                ('owners', models.ManyToManyField(help_text='The person who has total ownership of the resource', related_name='owns_hs_core_genericresource', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='genericresources', verbose_name='Author', on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('view_groups', models.ManyToManyField(help_text='This is the set of Hydroshare Groups who can view the resource', related_name='group_viewable_hs_core_genericresource', null=True, to='auth.Group', blank=True)),
                ('view_users', models.ManyToManyField(help_text='This is the set of Hydroshare Users who can view the resource', related_name='user_viewable_hs_core_genericresource', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
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
                ('group', models.ForeignKey(on_delete=models.CASCADE, to='auth.Group')),
                ('owner', models.ForeignKey(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
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
                ('content_type', models.ForeignKey(related_name='hs_core_identifier_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('code', models.CharField(max_length=3, choices=[('aar', 'Afar'), ('abk', 'Abkhazian'), ('ace', 'Achinese'), ('ach', 'Acoli'), ('ada', 'Adangme'), ('ady', 'Adyghe; Adygei'), ('afa', 'Afro-Asiatic languages'), ('afh', 'Afrihili'), ('afr', 'Afrikaans'), ('ain', 'Ainu'), ('aka', 'Akan'), ('akk', 'Akkadian'), ('al', 'Albanian'), ('ale', 'Aleut'), ('alg', 'Algonquian languages'), ('alt', 'Southern Altai'), ('amh', 'Amharic'), ('ang', 'English, Old (ca.450-1100)'), ('anp', 'Angika'), ('apa', 'Apache languages'), ('ara', 'Arabic'), ('arc', 'Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)'), ('arg', 'Aragonese'), ('arm', 'Armenian'), ('arn', 'Mapudungun; Mapuche'), ('arp', 'Arapaho'), ('art', 'Artificial languages'), ('arw', 'Arawak'), ('asm', 'Assamese'), ('ast', 'Asturian; Bable; Leonese; Asturleonese'), ('ath', 'Athapascan languages'), ('aus', 'Australian languages'), ('ava', 'Avaric'), ('ave', 'Avestan'), ('awa', 'Awadhi'), ('aym', 'Aymara'), ('aze', 'Azerbaijani'), ('bad', 'Banda languages'), ('bai', 'Bamileke languages'), ('bak', 'Bashkir'), ('bal', 'Baluchi'), ('bam', 'Bambara'), ('ban', 'Balinese'), ('baq', 'Basque'), ('bas', 'Basa'), ('bat', 'Baltic languages'), ('bej', 'Beja; Bedawiyet'), ('bel', 'Belarusian'), ('bem', 'Bemba'), ('ben', 'Bengali'), ('ber', 'Berber languages'), ('bho', 'Bhojpuri'), ('bih', 'Bihari languages'), ('bik', 'Bikol'), ('bin', 'Bini; Edo'), ('bis', 'Bislama'), ('bla', 'Siksika'), ('bnt', 'Bantu languages'), ('ti', 'Tibetan'), ('bos', 'Bosnian'), ('bra', 'Braj'), ('bre', 'Breton'), ('btk', 'Batak languages'), ('bua', 'Buriat'), ('bug', 'Buginese'), ('bul', 'Bulgarian'), ('bur', 'Burmese'), ('byn', 'Blin; Bilin'), ('cad', 'Caddo'), ('cai', 'Central American Indian languages'), ('car', 'Galibi Cari'), ('cat', 'Catalan; Valencian'), ('cau', 'Caucasian languages'), ('ce', 'Cebuano'), ('cel', 'Celtic languages'), ('cze', 'Czech'), ('cha', 'Chamorro'), ('ch', 'Chibcha'), ('che', 'Chechen'), ('chg', 'Chagatai'), ('chi', 'Chinese'), ('chk', 'Chuukese'), ('chm', 'Mari'), ('chn', 'Chinook jargon'), ('cho', 'Choctaw'), ('chp', 'Chipewyan; Dene Suline'), ('chr', 'Cherokee'), ('chu', 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'), ('chv', 'Chuvash'), ('chy', 'Cheyenne'), ('cmc', 'Chamic languages'), ('cop', 'Coptic'), ('cor', 'Cornish'), ('cos', 'Corsican'), ('cpe', 'Creoles and pidgins, English based'), ('cpf', 'Creoles and pidgins, French-based'), ('cpp', 'Creoles and pidgins, Portuguese-based'), ('cre', 'Cree'), ('crh', 'Crimean Tatar; Crimean Turkish'), ('crp', 'Creoles and pidgins'), ('cs', 'Kashubian'), ('cus', 'Cushitic languages'), ('wel', 'Welsh'), ('dak', 'Dakota'), ('dan', 'Danish'), ('dar', 'Dargwa'), ('day', 'Land Dayak languages'), ('del', 'Delaware'), ('den', 'Slave (Athapascan)'), ('ger', 'German'), ('dgr', 'Dogri'), ('din', 'Dinka'), ('div', 'Divehi; Dhivehi; Maldivian'), ('doi', 'Dogri'), ('dra', 'Dravidian languages'), ('ds', 'Lower Sorbian'), ('dua', 'Duala'), ('dum', 'Dutch, Middle (ca.1050-1350)'), ('dut', 'Dutch; Flemish'), ('dyu', 'Dyula'), ('dzo', 'Dzongkha'), ('efi', 'Efik'), ('egy', 'Egyptian (Ancient)'), ('eka', 'Ekajuk'), ('gre', 'Greek, Modern (1453-)'), ('elx', 'Elamite'), ('eng', 'English'), ('enm', 'English, Middle (1100-1500)'), ('epo', 'Esperanto'), ('est', 'Estonian'), ('ewe', 'Ewe'), ('ewo', 'Ewondo'), ('fan', 'Fang'), ('fao', 'Faroese'), ('per', 'Persian'), ('fat', 'Fanti'), ('fij', 'Fijian'), ('fil', 'Filipino; Pilipino'), ('fin', 'Finnish'), ('fiu', 'Finno-Ugrian languages'), ('fon', 'Fon'), ('fre', 'French'), ('frm', 'French, Middle (ca.1400-1600)'), ('fro', 'French, Old (842-ca.1400)'), ('frr', 'Northern Frisian'), ('frs', 'Eastern Frisian'), ('fry', 'Western Frisian'), ('ful', 'Fulah'), ('fur', 'Friulian'), ('gaa', 'Ga'), ('gay', 'Gayo'), ('gba', 'Gbaya'), ('gem', 'Germanic languages'), ('geo', 'Georgian'), ('gez', 'Geez'), ('gil', 'Gilbertese'), ('gla', 'Gaelic; Scottish Gaelic'), ('gle', 'Irish'), ('glg', 'Galician'), ('glv', 'Manx'), ('gmh', 'German, Middle High (ca.1050-1500)'), ('goh', 'German, Old High (ca.750-1050)'), ('gon', 'Gondi'), ('gor', 'Gorontalo'), ('got', 'Gothic'), ('gr', 'Grebo'), ('grc', 'Greek, Ancient (to 1453)'), ('grn', 'Guarani'), ('gsw', 'Swiss German; Alemannic; Alsatian'), ('guj', 'Gujarati'), ('gwi', b"Gwich'in"), ('hai', 'Haida'), ('hat', 'Haitian; Haitian Creole'), ('hau', 'Hausa'), ('haw', 'Hawaiian'), ('he', 'Hebrew'), ('her', 'Herero'), ('hil', 'Hiligaynon'), ('him', 'Himachali languages; Western Pahari languages'), ('hin', 'Hindi'), ('hit', 'Hittite'), ('hmn', 'Hmong; Mong'), ('hmo', 'Hiri Motu'), ('hrv', 'Croatian'), ('hs', 'Upper Sorbian'), ('hun', 'Hungarian'), ('hup', 'Hupa'), ('iba', 'Iban'), ('ibo', 'Igbo'), ('ice', 'Icelandic'), ('ido', 'Ido'), ('iii', 'Sichuan Yi; Nuosu'), ('ijo', 'Ijo languages'), ('iku', 'Inuktitut'), ('ile', 'Interlingue; Occidental'), ('ilo', 'Iloko'), ('ina', 'Interlingua (International Auxiliary Language Association)'), ('inc', 'Indic languages'), ('ind', 'Indonesian'), ('ine', 'Indo-European languages'), ('inh', 'Ingush'), ('ipk', 'Inupiaq'), ('ira', 'Iranian languages'), ('iro', 'Iroquoian languages'), ('ita', 'Italian'), ('jav', 'Javanese'), ('jbo', 'Lojban'), ('jpn', 'Japanese'), ('jpr', 'Judeo-Persian'), ('jr', 'Judeo-Arabic'), ('kaa', 'Kara-Kalpak'), ('ka', 'Kabyle'), ('kac', 'Kachin; Jingpho'), ('kal', 'Kalaallisut; Greenlandic'), ('kam', 'Kamba'), ('kan', 'Kannada'), ('kar', 'Karen languages'), ('kas', 'Kashmiri'), ('kau', 'Kanuri'), ('kaw', 'Kawi'), ('kaz', 'Kazakh'), ('kbd', 'Kabardian'), ('kha', 'Khasi'), ('khi', 'Khoisan languages'), ('khm', 'Central Khmer'), ('kho', 'Khotanese; Sakan'), ('kik', 'Kikuyu; Gikuyu'), ('kin', 'Kinyarwanda'), ('kir', 'Kirghiz; Kyrgyz'), ('km', 'Kimbundu'), ('kok', 'Konkani'), ('kom', 'Komi'), ('kon', 'Kongo'), ('kor', 'Korean'), ('kos', 'Kosraean'), ('kpe', 'Kpelle'), ('krc', 'Karachay-Balkar'), ('krl', 'Karelian'), ('kro', 'Kru languages'), ('kru', 'Kurukh'), ('kua', 'Kuanyama; Kwanyama'), ('kum', 'Kumyk'), ('kur', 'Kurdish'), ('kut', 'Kutenai'), ('lad', 'Ladino'), ('lah', 'Lahnda'), ('lam', 'Lamba'), ('lao', 'Lao'), ('lat', 'Latin'), ('lav', 'Latvian'), ('lez', 'Lezghian'), ('lim', 'Limburgan; Limburger; Limburgish'), ('lin', 'Lingala'), ('lit', 'Lithuanian'), ('lol', 'Mongo'), ('loz', 'Lozi'), ('ltz', 'Luxembourgish; Letzeburgesch'), ('lua', 'Luba-Lulua'), ('lu', 'Luba-Katanga'), ('lug', 'Ganda'), ('lui', 'Luiseno'), ('lun', 'Lunda'), ('luo', 'Luo (Kenya and Tanzania)'), ('lus', 'Lushai'), ('mac', 'Macedonian'), ('mad', 'Madurese'), ('mag', 'Magahi'), ('mah', 'Marshallese'), ('mai', 'Maithili'), ('mak', 'Makasar'), ('mal', 'Malayalam'), ('man', 'Mandingo'), ('mao', 'Maori'), ('map', 'Austronesian languages'), ('mar', 'Marathi'), ('mas', 'Masai'), ('may', 'Malay'), ('mdf', 'Moksha'), ('mdr', 'Mandar'), ('men', 'Mende'), ('mga', 'Irish, Middle (900-1200)'), ('mic', b"Mi'kmaq; Micmac"), ('min', 'Minangkabau'), ('mis', 'Uncoded languages'), ('mkh', 'Mon-Khmer languages'), ('mlg', 'Malagasy'), ('mlt', 'Maltese'), ('mnc', 'Manchu'), ('mni', 'Manipuri'), ('mno', 'Manobo languages'), ('moh', 'Mohawk'), ('mon', 'Mongolian'), ('mos', 'Mossi'), ('mul', 'Multiple languages'), ('mun', 'Munda languages'), ('mus', 'Creek'), ('mwl', 'Mirandese'), ('mwr', 'Marwari'), ('myn', 'Mayan languages'), ('myv', 'Erzya'), ('nah', 'Nahuatl languages'), ('nai', 'North American Indian languages'), ('nap', 'Neapolitan'), ('nau', 'Nauru'), ('nav', 'Navajo; Navaho'), ('nbl', 'Ndebele, South; South Ndebele'), ('nde', 'Ndebele, North; North Ndebele'), ('ndo', 'Ndonga'), ('nds', 'Low German; Low Saxon; German, Low; Saxon, Low'), ('nep', 'Nepali'), ('new', 'Nepal Bhasa; Newari'), ('nia', 'Nias'), ('nic', 'Niger-Kordofanian languages'), ('niu', 'Niuean'), ('nno', 'Norwegian Nynorsk; Nynorsk, Norwegian'), ('no', 'Bokmal, Norwegian; Norwegian Bokmal'), ('nog', 'Nogai'), ('non', 'Norse, Old'), ('nor', 'Norwegian'), ('nqo', b"N'Ko"), ('nso', 'Pedi; Sepedi; Northern Sotho'), ('nu', 'Nubian languages'), ('nwc', 'Classical Newari; Old Newari; Classical Nepal Bhasa'), ('nya', 'Chichewa; Chewa; Nyanja'), ('nym', 'Nyamwezi'), ('nyn', 'Nyankole'), ('nyo', 'Nyoro'), ('nzi', 'Nzima'), ('oci', 'Occitan (post 1500)'), ('oji', 'Ojibwa'), ('ori', 'Oriya'), ('orm', 'Oromo'), ('osa', 'Osage'), ('oss', 'Ossetian; Ossetic'), ('ota', 'Turkish, Ottoman (1500-1928)'), ('oto', 'Otomian languages'), ('paa', 'Papuan languages'), ('pag', 'Pangasinan'), ('pal', 'Pahlavi'), ('pam', 'Pampanga; Kapampangan'), ('pan', 'Panjabi; Punjabi'), ('pap', 'Papiamento'), ('pau', 'Palauan'), ('peo', 'Persian, Old (ca.600-400 B.C.)'), ('phi', 'Philippine languages'), ('phn', 'Phoenician'), ('pli', 'Pali'), ('pol', 'Polish'), ('pon', 'Pohnpeian'), ('por', 'Portuguese'), ('pra', 'Prakrit languages'), ('pro', 'Provencal, Old (to 1500);Occitan, Old (to 1500)'), ('pus', 'Pushto; Pashto'), ('qaa-qtz', 'Reserved for local use'), ('que', 'Quechua'), ('raj', 'Rajasthani'), ('rap', 'Rapanui'), ('rar', 'Rarotongan; Cook Islands Maori'), ('roa', 'Romance languages'), ('roh', 'Romansh'), ('rom', 'Romany'), ('rum', 'Romanian; Moldavian; Moldovan'), ('run', 'Rundi'), ('rup', 'Aromanian; Arumanian; Macedo-Romanian'), ('rus', 'Russian'), ('sad', 'Sandawe'), ('sag', 'Sango'), ('sah', 'Yakut'), ('sai', 'South American Indian languages'), ('sal', 'Salishan languages'), ('sam', 'Samaritan Aramaic'), ('san', 'Sanskrit'), ('sas', 'Sasak'), ('sat', 'Santali'), ('scn', 'Sicilian'), ('sco', 'Scots'), ('sel', 'Selkup'), ('sem', 'Semitic languages'), ('sga', 'Irish, Old (to 900)'), ('sgn', 'Sign Languages'), ('shn', 'Shan'), ('sid', 'Sidamo'), ('sin', 'Sinhala; Sinhalese'), ('sio', 'Siouan languages'), ('sit', 'Sino-Tibetan languages'), ('sla', 'Slavic languages'), ('slo', 'Slovak'), ('slv', 'Slovenian'), ('sma', 'Southern Sami'), ('sme', 'Northern Sami'), ('smi', 'Sami languages'), ('smj', 'Lule Sami'), ('smn', 'Inari Sami'), ('smo', 'Samoan'), ('sms', 'Skolt Sami'), ('sna', 'Shona'), ('snd', 'Sindhi'), ('snk', 'Soninke'), ('sog', 'Sogdian'), ('som', 'Somali'), ('son', 'Songhai languages'), ('sot', 'Sotho, Southern'), ('spa', 'Spanish; Castilian'), ('srd', 'Sardinian'), ('srn', 'Sranan Tongo'), ('srp', 'Serbian'), ('srr', 'Serer'), ('ssa', 'Nilo-Saharan languages'), ('ssw', 'Swati'), ('suk', 'Sukuma'), ('sun', 'Sundanese'), ('sus', 'Susu'), ('sux', 'Sumerian'), ('swa', 'Swahili'), ('swe', 'Swedish'), ('syc', 'Classical Syriac'), ('syr', 'Syriac'), ('tah', 'Tahitian'), ('tai', 'Tai languages'), ('tam', 'Tamil'), ('tat', 'Tatar'), ('tel', 'Telugu'), ('tem', 'Timne'), ('ter', 'Tereno'), ('tet', 'Tetum'), ('tgk', 'Tajik'), ('tgl', 'Tagalog'), ('tha', 'Thai'), ('tig', 'Tigre'), ('tir', 'Tigrinya'), ('tiv', 'Tiv'), ('tkl', 'Tokelau'), ('tlh', 'Klingon; tlhIngan-Hol'), ('tli', 'Tlingit'), ('tmh', 'Tamashek'), ('tog', 'Tonga (Nyasa)'), ('ton', 'Tonga (Tonga Islands)'), ('tpi', 'Tok Pisin'), ('tsi', 'Tsimshian'), ('tsn', 'Tswana'), ('tso', 'Tsonga'), ('tuk', 'Turkmen'), ('tum', 'Tumbuka'), ('tup', 'Tupi languages'), ('tur', 'Turkish'), ('tut', 'Altaic languages'), ('tvl', 'Tuvalu'), ('twi', 'Twi'), ('tyv', 'Tuvinian'), ('udm', 'Udmurt'), ('uga', 'Ugaritic'), ('uig', 'Uighur; Uyghur'), ('ukr', 'Ukrainian'), ('um', 'Umbundu'), ('und', 'Undetermined'), ('urd', 'Urdu'), ('uz', 'Uzbek'), ('vai', 'Vai'), ('ven', 'Venda'), ('vie', 'Vietnamese'), ('vol', 'Volapuk'), ('vot', 'Votic'), ('wak', 'Wakashan languages'), ('wal', 'Wolaitta; Wolaytta'), ('war', 'Waray'), ('was', 'Washo'), ('wen', 'Sorbian languages'), ('wln', 'Walloon'), ('wol', 'Wolof'), ('xal', 'Kalmyk; Oirat'), ('xho', 'Xhosa'), ('yao', 'Yao'), ('yap', 'Yapese'), ('yid', 'Yiddish'), ('yor', 'Yoruba'), ('ypk', 'Yupik languages'), ('zap', 'Zapotec'), ('zbl', 'Blissymbols; Blissymbolics; Bliss'), ('zen', 'Zenaga'), ('zgh', 'Standard Moroccan Tamazight'), ('zha', 'Zhuang; Chuang'), ('znd', 'Zande languages'), ('zul', 'Zulu'), ('zun', 'Zuni'), ('zxx', 'No linguistic content; Not applicable'), ('zza', 'Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki')])),
                ('content_type', models.ForeignKey(related_name='hs_core_language_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_publisher_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('type', models.CharField(max_length=100, choices=[('isPartOf', 'Part Of'), ('isExecutedBy', 'Executed By'), ('isCreatedBy', 'Created By'), ('isVersionOf', 'Version Of'), ('isDataFor', 'Data For'), ('cites', 'Cites')])),
                ('value', models.CharField(max_length=500)),
                ('content_type', models.ForeignKey(related_name='hs_core_relation_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('resource_file', models.FileField(storage=django_irods.storage.S3Storage(), max_length=500, upload_to=hs_core.models.get_path)),
                ('content_type', models.ForeignKey(on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_rights_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_source_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_subject_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_title_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
                ('content_type', models.ForeignKey(related_name='hs_core_type_related', on_delete=models.CASCADE, to='contenttypes.ContentType')),
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
