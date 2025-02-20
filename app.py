import boto3


s3 = boto3.client('s3')


bucket_name = 'soccer-predictor-web-scrape' 
#file_key = 'team_standings.csv'  
file_key ='last_five_form.csv'

try:
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    file_content = response['Body'].read().decode('utf-8')  # Decode from bytes to string

    print('File retrieved successfully:')
    print(file_content)
except Exception as e:
    print(f"Error retrieving file: {e}")
