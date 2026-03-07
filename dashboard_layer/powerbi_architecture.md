# Power BI Dashboard Architecture

## Overview

This document describes the architecture and layout of the Power BI dashboards used in the MRV system.  
The dashboards are designed to provide insights into carbon emissions, monitoring activities, and validation processes.

---

## Dashboard Pages

The dashboard will contain the following pages:

1. Overview Dashboard  
   Displays high-level KPIs related to carbon emissions and farms.

2. Carbon Emissions Dashboard  
   Shows detailed emission data by farm, activity, and time period.

3. Monitoring Dashboard  
   Tracks ongoing monitoring activities and environmental data.

4. Validation Dashboard  
   Used for verifying emission records and ensuring data accuracy.

---

## KPI Card Placement

Key Performance Indicators (KPIs) will be displayed at the top of the Overview page.

Examples of KPIs:

- Total Carbon Emissions
- Total Carbon Offset
- Total Farms Monitored
- Total Activities Recorded

---

## Filters

Global filters will allow users to refine the data displayed in the dashboard.

Common filters include:

- Date Range
- Farm Location
- Activity Type

These filters will be applied across multiple dashboard pages.

---

## Drill-Through Logic

Users will be able to navigate deeper into the data using drill-through functionality.

Example navigation flow:

Overview Dashboard → Farm Details → Activity Level Data

This allows users to analyze emission data at different levels.

---

## Role-Based View Logic

Different users will have different levels of access to the dashboard.

Admin  
Full access to all dashboards and data.

Validator  
Access to validation dashboards and emission verification data.

Farm Manager  
Access to dashboards related only to their farm.
