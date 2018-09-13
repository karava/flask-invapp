from flask import Flask, render_template, request, redirect, url_for, flash
from boto3.dynamodb.conditions import Key, Attr
from flask_dynamo import Dynamo
import os
import boto3
import json

S3_BUCKET = 'invapp1'

with open('config.json', 'r') as f:
    parameters = json.load(f)

for environ in parameters['environs'].keys():
    os.environ[environ] = parameters['environs'][environ]

s3_resource = boto3.resource(
   "s3",
   aws_access_key_id=parameters['environs']['AWS_ACCESS_KEY_ID'],
   aws_secret_access_key=parameters['environs']['AWS_SECRET_ACCESS_KEY']
)

app = Flask(__name__)
app.secret_key = 'secret' #for flask flash messages

@app.route("/")
def hello():
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('invapp')
    table = table.scan() #prints out a dictionary
    items = table['Items'] #items is a list of dictionaries

    # Create dictionaries for items, need all labels and the image url
    tops = {}
    bottoms = {}
    otheritem = {}

    tops_labels = ['Sweater', 'Long Sleeve', 'Jacket']
    bottoms_labels = ['Denim', 'Jeans']

    for i in range(len(items)):
        if any(x in items[i]['Labels'] for x in tops_labels):
            tops[items[i]['itemname']] = items[i]['Labels']
        elif any(x in items[i]['Labels'] for x in bottoms_labels):
            bottoms[items[i]['itemname']] = items[i]['Labels']
        else:
            otheritem[items[i]['itemname']] = items[i]['Labels']

    # print(otheritem)
    return render_template('index.html', tops=tops, bottoms=bottoms, otheritem=otheritem)
    # return "Hello World!"


@app.route('/files')
def files():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket('invapp1')
    summaries = my_bucket.objects.all()
    return render_template('files.html', my_bucket=my_bucket, files=summaries)


@app.route('/upload', methods=['POST'])
def upload():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(S3_BUCKET)

    upload_files = request.files.getlist('file')

    for file in upload_files:
        my_bucket.Object(file.filename).put(Body=file)

    flash('File uploaded successfully')
    return redirect(url_for('files'))


@app.route('/delete', methods=['POST'])
def delete():
    key = request.form['key']

    #delete item from s3 bucket
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(S3_BUCKET)
    my_bucket.Object(key).delete()

    #delete item from dynamdb table
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('invapp')
    response = table.scan(FilterExpression=Attr('itemname').eq(key))
    delitem = response['Items']

    table.delete_item(
        Key={
            'itemid': delitem[0]['itemid'],
            'timestamp': delitem[0]['timestamp'],
        }
    )

    flash('File deleted successfully')
    return redirect(url_for('files'))

if __name__ == "__main__":
    app.run(debug=True)