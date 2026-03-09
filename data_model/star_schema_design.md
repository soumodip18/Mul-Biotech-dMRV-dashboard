# MRV Core – Star Schema Data Model

## Overview

This document describes the star schema used for the MRV (Monitoring, Reporting, and Verification) system.  
The schema is designed to support analytical queries and Power BI dashboards for monitoring carbon emissions from agricultural activities.

The model consists of one **Fact Table** and multiple **Dimension Tables**.

---

# Fact Table

## fact_carbon_emission

The fact table stores measurable carbon emission data generated from farm activities.

### Primary Key
emission_id

### Foreign Keys
farm_id  
activity_id  
date_id  

### Measures
emission_value – Amount of carbon emitted  
carbon_offset – Amount of carbon offset or reduced  

---

# Dimension Tables

## dim_farm

Stores descriptive information about farms.

Primary Key  
farm_id  

Attributes
- farm_name
- location
- farmer_name

---

## dim_activity

Stores information about agricultural activities that generate emissions.

Primary Key  
activity_id  

Attributes
- activity_type
- category

---

## dim_date

Stores date information used for time-based analysis.

Primary Key  
date_id  

Attributes
- date
- month
- year

---

# Relationships

The fact table connects to dimension tables using foreign keys.

fact_carbon_emission → dim_farm (Many-to-One)  
fact_carbon_emission → dim_activity (Many-to-One)  
fact_carbon_emission → dim_date (Many-to-One)  

---

# Cardinality

- One Farm can have many emission records
- One Activity can appear in many emission records
- One Date can contain multiple emission entries

This structure enables efficient filtering and aggregation in analytics tools such as Power BI.
