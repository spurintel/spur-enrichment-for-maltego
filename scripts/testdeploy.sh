gcloud builds submit --tag gcr.io/jack-testing-5150/spur-enrichment-for-maltego
gcloud run deploy staging-spur-enrichment-for-maltego --image gcr.io/jack-testing-5150/spur-enrichment-for-maltego --platform managed --region=us-east1
