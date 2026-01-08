# 🚀 Real-Time Data Integration and Analytics on Confluent Cloud

This workshop, **"Building Real-Time Streaming Pipelines on Confluent Cloud Using Kafka, Connectors, and Flink,"** provides hands-on experience in constructing a complete, low-latency data pipeline. You will learn to integrate external databases using fully-managed **Confluent Fully Managed Connectors** and process data in real-time with **Confluent Apache Flink**.

---

## 🎯 Objective

The core goal is to build an **end-to-end real-time data pipeline** on Confluent Cloud. This covers two main phases:

1.  **Data Ingestion (Connectors):** Establish continuous data flow between a PostgreSQL database and Kafka using fully-managed **Postgres CDC Source** and **Postgres Sink** connectors for reliable, scalable data movement.
2.  **Stream Processing (Flink):** Utilize **Flink** to query, enrich, aggregate, and analyze the live Kafka streams, generating crucial real-time business metrics that power a live dashboard.

---

## 🏗️ Architecture Overview

The pipeline streams change data from a source database, moves it through Kafka, is transformed by Flink, and is then replicated to a target database while simultaneously feeding a real-time dashboard.

---

## 📚 Workshop Labs

### 🧩 Lab 1: Data Ingestion with Confluent Connectors

This lab focuses on the integration layer, utilizing Confluent's fully-managed connectors to achieve seamless Change Data Capture (CDC) and data replication.

| Step | Focus | Outcome |
| :--- | :--- | :--- |
| **1-3** | **Cloud Setup** | Cluster, Environment, and API Key creation. |
| **4** | **Source Connector** | Deploy **Postgres CDC Source V2** to stream database changes to Kafka. |
| **5** | **Test Data Flow** | Insert data into the source DB and verify messages appear in the Kafka topic. |
| **6-7** | **Sink Connector** | Deploy **Postgres Sink** to replicate data from Kafka to a target database schema. |
| **8** | **Replication Check** | Verify real-time updates and deletes are reflected in the destination database. |

➡️ **[Continue to Lab 1 Guide for Detailed Steps](Lab-1.md)**

---

### ⚡ Lab 2: Real-Time Stream Processing using Confluent Apache Flink

This lab explores stream analytics, transforming raw event data into meaningful metrics using Flink SQL.

| Step | Focus | Outcome |
| :--- | :--- | :--- |
| **4-9** | **Configuration & Producers** | Set up the API keys, populate the data, and start the continuous **sales event stream**. |
| **10-11** | **Flink Workspace** | Provision a **Flink Compute Pool** and open the Flink SQL interface. |
| **12** | **Flink SQL Execution** | Run multiple jobs, including: **Stream-Table Joins** for enrichment, **Tumbling Windows** (1-minute trends), **Hopping Windows** (5-minute rolling sums), and **Continuous Aggregations** (total revenue). |
| **13-14** | **Dashboard Analysis** | Run the application and observe live, Flink-powered charts reflecting real-time sales metrics. |

➡️ **[Continue to Lab 2 Guide for Detailed Steps](Lab-2.md)**

---
## Labs

Next Lab: **[Lab 1: Data Ingestion with Confluent Connectors](Lab-1.md)**

---
