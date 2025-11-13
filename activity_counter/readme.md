# Retrieving lost downloads data from our metrics exports

We had several months in 2025 between [3.0.0](https://github.com/hydroshare/hydroshare/releases/tag/3.0.0) Feb 5th and [3.11.1](https://github.com/hydroshare/hydroshare/releases/tag/3.11.1) on Nov 10th where we were failing to update the download counter in the AbstractResource class.

This approach goes back to the metrics logs that are exported monthly from the hs_tracking table. We have to use the logs instead of the db because we truncate the db table to a rolling window of 60 days.

Here's the approach that I took:

1. Download tracking variable exports from GCP. More info here: [yesterdays-variables](https://develop.cuahsi.io/hydroshare/metrics/#yesterdays-variables)
2. Put all of the relevant .csv files into this dir. For example:
    * gs://hydroshare-stats-pg-dumps/production/2025-11-13/hs_tracking_variable_2025-11-01_2025-11-13.csv (this is a partial export run mannually to capture the data in Nov 2025)
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
    - Usage example: `python activity_counter.py "2025-02-05" "2025-11-10" "download" --chunk-size 50000 --directory "input" --output "output/2025-02-05_to_2025-11-10.csv"`
    - [3.0.0](https://github.com/hydroshare/hydroshare/releases/tag/3.0.0) was feb 5th. Csv exports give us data up to 11/1/2025. [3.11.1](https://github.com/hydroshare/hydroshare/releases/tag/3.11.1) was Nov 10th. So need to also export the downloads from hs_tracking table in the db for that 11/1 to 11/10 range and add those in as well. [Here's how I did that](https://github.com/CUAHSI/platform-recipes/pull/143)
4. Copy the files into one of the hs pods
    - `export HS_POD=$(kubectl get pods -l app=hydroshare -o jsonpath="{.items[0].metadata.name}")`
    - `kubectl cp output/2025-02-05_to_2025-11-10.csv $HS_POD:/tmp/2025-02-05_to_2025-11-10.csv`
    - Copy the management command if not deployed...
      * `kubectl cp ../hs_core/management/commands/update_download_counts.py $HS_POD:/hydroshare/hs_core/management/commands/update_download_counts.py`
5. Dry run: Ingest the new counts into Django:
    - `kubectl exec $HS_POD -- python manage.py update_download_counts /tmp/2025-02-05_to_2025-11-10.csv --dry-run`
6. If satisfied, ingest the counts for realz