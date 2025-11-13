1. Download tracking variable exports from GCP. More info here: [yesterdays-variables](https://develop.cuahsi.io/hydroshare/metrics/#yesterdays-variables)
2. Put all of the relevant .csv files into this dir
3. Run the script, passing the start date, end date, and activity type
Usage example: 
`python activity_counter.py "2025-10-01" "2025-10-03" "download" --output "my_results.csv"`
