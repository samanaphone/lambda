# Samana TechSupport call management with Nexmo


INSTALL

To be able to implement this code on AWS Lambda a new Amazon EC2 Linux Image. 

Possible needed packages:
* sudo yum install libffi-devel
* sudo yum install gcc
* sudo yum install openssl-devel
* sudo yum install python27-boto3

DOCKER

docker run -it --rm --name samanaphone --mount type=bind,source=$(pwd),target=/usr/src ubuntu:focal /bin/bash
# Inside the container:
# need to copy aws keys into /usr/src
apt update
apt install -y python3-pip zip curl groff less
mkdir -p /usr/src/aws
cd /usr/src/aws
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
mkdir -p /root/.aws
cp /usr/src/config /usr/src/credentials /root/.aws
