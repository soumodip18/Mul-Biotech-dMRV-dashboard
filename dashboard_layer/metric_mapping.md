# KPI Metric Mapping

## Overview

This document defines the mapping between dashboard KPIs and the underlying data model.  
Each KPI specifies the source table, calculation logic, dependencies, and validation conditions used in the Power BI dashboard.

---

## KPI Definitions

| KPI Name | Source Table | DAX Formula | Dependency | Validation Condition |
|---------|-------------|-------------|------------|----------------------|
| Total Carbon Emission | fact_carbon_emission | SUM(emission_value) | date_id | Emission value must be greater than 0 |
| Total Carbon Offset | fact_carbon_emission | SUM(carbon_offset) | farm_id | Offset values must be valid |
| Total Farms | dim_farm | COUNT(farm_id) | None | farm_id must be unique |
| Total Activities | dim_activity | COUNT(activity_id) | None | activity_id must be valid |

---

## Description

### Total Carbon Emission
Represents the total carbon emissions generated from farm activities.

### Total Carbon Offset
Represents the total amount of carbon emissions offset through sustainable practices.

### Total Farms
Represents the number of farms included in the MRV monitoring system.

### Total Activities
Represents the total number of agricultural activities recorded.
