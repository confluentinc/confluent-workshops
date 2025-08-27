terraform {
  required_providers {
    tls = {
      source  = "hashicorp/tls"
      version = "4.0.5"
    }
    local = {
      source = "hashicorp/local"
      version = "2.5.1"
    }
  }
}

# ---------------------------------------------------------

provider "aws" {
  region = "us-east-1"
}

# Create the VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "osk-cc-migration-workshop"
  }
}

# Create the Internet Gateway (IGW)
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "My-Public-VPC-IGW"
  }
}

# Create the Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a" 

  map_public_ip_on_launch = true

  tags = {
    Name = "osk-cc-migration-workshop-public-subnet"
  }
}

# Create a custom Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  # This route sends all internet-bound traffic (0.0.0.0/0) to the Internet Gateway.
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "My-Public-Route-Table"
  }
}

# Associate the Route Table with the Public Subnet
resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public_rt.id
}

# ---------------------------------------------------------

# Generate a new private key using the TLS provider
resource "tls_private_key" "rsa_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Create the key pair in AWS using the public key from the generated key
resource "aws_key_pair" "generated_key" {
  key_name   = "my-tf-generated-key"
  public_key = tls_private_key.rsa_key.public_key_openssh
}

# Save the generated private key to a local file
resource "local_file" "private_key_pem" {
  content  = tls_private_key.rsa_key.private_key_pem
  filename = "${path.module}/my-tf-key.pem"
  file_permission = "0400" # Set correct permissions
}

# ---------------------------------------------------------


resource "aws_security_group" "kafka_sg" {
  name        = "kafka-sg"
  description = "Allow Kafka and SSH access"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kafka Port"
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Zookeeper Port"
    from_port   = 2181
    to_port     = 2181
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
}

# ---------------------------------------------------------


output "ec2_instance_vpc_id" {
  description = "The VPC ID of the newly created EC2 instance."
  value       = aws_vpc.main.id
}

output "kafka_public_ip" {
  description = "The public IP address of the EC2 instance."
  value       = aws_instance.kafka_ec2.public_ip
}

output "jumpbox_public_ip" {
  description = "The public IP address of the EC2 instance."
  value       = aws_instance.jumpbox_ec2.public_ip
}


# ---------------------------------------------------------


resource "aws_instance" "kafka_ec2" {
  ami                    = "ami-05ffe3c48a9991133" # Amazon Linux 2 AMI
  instance_type          = "t2.medium"
  subnet_id              = aws_subnet.public.id
  key_name               = aws_key_pair.generated_key.key_name
  vpc_security_group_ids = [aws_security_group.kafka_sg.id]

  # This block customizes the root (/) volume
  root_block_device {
    volume_size = 50      # Size in GiB
    volume_type = "gp3"   # General Purpose SSD (recommended)
    delete_on_termination = true # The volume will be deleted when the instance is terminated
  }

  user_data = <<-EOF
              #!/bin/bash
              
              # Redirect all output to a log file for debugging
              exec > /tmp/user_data.log 2>&1

              # Install Java
              yum update -y
              wget https://corretto.aws/downloads/latest/amazon-corretto-17-x64-linux-jdk.rpm
              sudo yum localinstall -y amazon-corretto-17-x64-linux-jdk.rpm

              # Download and extract Kafka
              cd /opt
              curl -O https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz
              tar -xzf kafka_2.13-3.9.0.tgz
              mv kafka_2.13-3.9.0 kafka

              # Extract the public IP of EC2 instance
              export EC2_PUBLIC_IP=$(curl -s ifconfig.me)

              # Update Kafka config
              sudo sed -i 's|^log.dirs=.*|log.dirs=/tmp/kafka-logs|' /opt/kafka/config/server.properties
              sudo sed -i 's|^#listeners=.*|listeners=PLAINTEXT://:9092|' /opt/kafka/config/server.properties
              sudo sed -i "s|^#advertised.listeners=.*|advertised.listeners=PLAINTEXT://$${EC2_PUBLIC_IP}:9092|" /opt/kafka/config/server.properties

              # Start Zookeeper
              nohup /opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties > /tmp/zookeeper.log 2>&1 &

              # Give Zookeeper time to start
              sleep 10

              # Start Kafka
              nohup /opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties > /tmp/kafka.log 2>&1 &

              # Install Confluent CLI
              curl -sL --http1.1 https://cnfl.io/cli | sh -s --
              sudo mv ./bin/confluent /usr/local/bin/

              # Install kafka-avro-console-consumer and kafka-avro-console-producer CLI
              curl -O https://packages.confluent.io/archive/8.0/confluent-community-8.0.0.tar.gz
              tar -xzf confluent-community-8.0.0.tar.gz
              sudo chown -R ec2-user:ec2-user /opt/confluent-8.0.0/
              
              # Set the PATH in .bash_profile file
              echo 'export PATH="$PATH:/opt/kafka/bin/:/opt/confluent-8.0.0/bin/"' >> /home/ec2-user/.bash_profile
              source /home/ec2-user/.bash_profile 


              EOF
    tags = {
    Name = "osk-cc-workshop-kafka-ec2"
    }
}


resource "aws_instance" "jumpbox_ec2" {
  ami                    = "ami-05ffe3c48a9991133" # Amazon Linux 2 AMI
  instance_type          = "t2.medium"
  subnet_id              = aws_subnet.public.id
  key_name               = aws_key_pair.generated_key.key_name
  vpc_security_group_ids = [aws_security_group.kafka_sg.id]

  # This block customizes the root (/) volume
  root_block_device {
    volume_size = 50      # Size in GiB
    volume_type = "gp3"   # General Purpose SSD (recommended)
    delete_on_termination = true # The volume will be deleted when the instance is terminated
  }

  user_data = <<-EOF
              #!/bin/bash
              
              # Redirect all output to a log file for debugging
              exec > /tmp/user_data.log 2>&1

              # Install Java
              yum update -y
              wget https://corretto.aws/downloads/latest/amazon-corretto-17-x64-linux-jdk.rpm
              sudo yum localinstall -y amazon-corretto-17-x64-linux-jdk.rpm

              # Download and extract Kafka
              cd /opt
              curl -O https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz
              tar -xzf kafka_2.13-3.9.0.tgz
              mv kafka_2.13-3.9.0 kafka

              # Install Confluent CLI
              curl -sL --http1.1 https://cnfl.io/cli | sh -s --
              sudo mv ./bin/confluent /usr/local/bin/

              # Install kafka-avro-console-consumer and kafka-avro-console-producer CLI
              curl -O https://packages.confluent.io/archive/8.0/confluent-community-8.0.0.tar.gz
              tar -xzf confluent-community-8.0.0.tar.gz
              sudo chown -R ec2-user:ec2-user /opt/confluent-8.0.0/
              
              # Set the PATH in .bash_profile file
              echo 'export PATH="$PATH:/opt/kafka/bin/:/opt/confluent-8.0.0/bin/"' >> /home/ec2-user/.bash_profile
              source /home/ec2-user/.bash_profile 


              EOF
    tags = {
    Name = "osk-cc-workshop-jumpbox"
    }
}
