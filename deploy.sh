#!/bin/bash

source ../reciclai-web-service/reciclai/bin/activate

cd ../mlops-logs/
./deploy.sh
cd ../mlops-charts/
./deploy.sh