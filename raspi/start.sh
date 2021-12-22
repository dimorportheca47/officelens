#!/usr/bin/env bash
# stop script on error
set -e
# sudo apt update
# sudo apt upgrade

sudo apt install libatlas-base-dev
# Check to see if root CA file exists, download if not
if [ ! -f ./root-CA.crt ]; then
  printf "\nDownloading AWS IoT Root CA certificate from AWS...\n"
  curl https://www.amazontrust.com/repository/AmazonRootCA1.pem > root-CA.crt
fi

# Check to see if AWS Device SDK for Python exists, download if not
if [ ! -d ./aws-iot-device-sdk-python ]; then
  printf "\nCloning the AWS SDK...\n"
  git clone https://github.com/aws/aws-iot-device-sdk-python.git
fi

# Check to see if AWS Device SDK for Python is already installed, install if not
if ! python3 -c "import awsiot" &> /dev/null; then
  printf "\nInstalling AWS SDK...\n"
  pushd aws-iot-device-sdk-python
  pip install awsiotsdk
  result=$?
  popd
  if [ $result -ne 0 ]; then
    printf "\nERROR: Failed to install SDK.\n"
    exit $result
  fi
fi

if ! python3 -c "import grovepi" &> /dev/null; then
  printf "\nInstalling grovepi...\n"
  git clone https://github.com/DexterInd/GrovePi
  pushd GrovePi/Script
  sudo chmod +x install.sh
  sudo ./install.sh
  popd
  if [ $result -ne 0 ]; then
    printf "\nERROR: Failed to install grovepi.\n"
    exit $result
  fi
fi


# run pub/sub sample app using certificates downloaded in package
printf "\nRunning pub/sub sample application...\n"
python3 sensor_v2.py --device_name a478fe7a-1075-11ec-b11d-77d6a1bbc6b9 -e "Your endpoint" -r root-CA.crt -c office-monitoring.cert.pem -k office-monitoring.private.key
