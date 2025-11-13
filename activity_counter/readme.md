1. Download tracking variable exports from GCP. More info here: [yesterdays-variables](https://develop.cuahsi.io/hydroshare/metrics/#yesterdays-variables)
2. Put all of the relevant .csv files into this dir. For example:
    * gs://hydroshare-stats-pg-dumps/production/2025-11-01/hs_tracking_variable_2025-10-01_2025-11-01.csv
    * gs://hydroshare-stats-pg-dumps/production/2025-10-01/hs_tracking_variable_2025-09-01_2025-10-01.csv
    * gs://hydroshare-stats-pg-dumps/production/2025-09-01/hs_tracking_variable_2025-08-01_2025-09-01.csv
    * gs://hydroshare-stats-pg-dumps/production/2025-08-01/hs_tracking_variable_2025-07-01_2025-08-01.csv
    * gs://hydroshare-stats-pg-dumps/production/2025-07-01/hs_tracking_variable_2025-06-01_2025-07-01.csv
    * gs://hydroshare-stats-pg-dumps/production/2025-06-01/hs_tracking_variable_2025-05-01_2025-06-01.csv
    * gs://hydroshare-stats-pg-dumps/production/2025-05-01/hs_tracking_variable_2025-04-01_2025-05-01.csv
    * gs://hydroshare-stats-pg-dumps/production/2025-04-01/hs_tracking_variable.csv (this one is unique, it is 25gb and has data 2018 - Mar 31, 2025. It will need to be renamed in order to work with the script)
        * Renamed it to `hs_tracking_variable_2016-07-01_2025-04-01.csv`
3. Run the script, passing the start date, end date, and activity type
Usage example: 
`python activity_counter.py "2025-02-05" "2025-11-01" "download" --chunk-size 50000 --directory "input" --output "output/2025-02-05_to_2025-11-01.csv"`
1. [3.0.0](https://github.com/hydroshare/hydroshare/releases/tag/3.0.0) was feb 5th. Csv exports give us data up to 11/1/2025. [3.11.1](https://github.com/hydroshare/hydroshare/releases/tag/3.11.1) was Nov 10th. So need to also export the downloads from hs_tracking table in the db for that 11/1 to 11/10 range and add those in as well.