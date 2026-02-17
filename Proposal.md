# Team D - Carbon & Forests Dashboard: Deforestation and CO₂ Emissions

# Sustainable Development Goal(s): Goal 13: Climate action & Goal 15: Life on land

* This project will facilitate the exploration and comparison of territorial CO₂ emissions and deforestation across countries and over time. By turning these datasets into searchable country pages, rankings, cross-dataset comparisons, users can identify trends, supporting education and more informed conversations about climate mitigation and forest conservation.
* Hopefully this will also help people realize the harm of deforestation and take actions to contribute to the protection of trees, since CO2 concentration rise has a direct negative impact on human, and the Earth as a whole.

# Features

## Feature 1: Search bar - Shows the the deforestation rate and ranking; and CO2 emission respectively of a certain country by year (2000-2025).
* Person responsible: Milly
* User story: As a general person interested in sustainability related topics, I can look up a country and year and see the deforestation rate of that country in that year.
* Acceptance Criteria:
  - Given the user is on the deforestation lookup page, when the user selects a valid country and a valid year, then the system displays a list showing the deforestation rate and ranking, and CO2 emission for that country in the selected year.
  - If the user inserts only a year, then it will display a list of CO2 emission and deforestation rate and ranking of all countries in that year.
  - If the user inserts only a country, then it will display the most recent year's deforestation rate and ranking, as well as CO2 emission.
  - If the user inserts an invalid year or an invalid country, outputs string "invalid year or country".
  
## Feature 2: Chart — Shows a line chart of a country’s deforestation rate over time (2000–2025), with an optional table below.
* Person responsible: Amery
* User story: As a general person interested in sustainability related topics, I can select a country and view a line chart of its deforestation rate from 2000–2025 so I can understand the trend over time.
* Acceptance Criteria: 
  - Given the user is on the deforestation trend page, when the user selects a valid country, then the system displays a line chart of deforestation rate for that country from 2000–2025 (or for all available years in that range).
  - The chart includes labeled axes (Year on x-axis, Deforestation Rate on y-axis) and displays units consistent with the dataset.
  - If the user inserts only a country, then the system displays the country’s ranking for the most recent year available (and shows which year was used).
  - If the user selects a country with missing values for some years, then the chart still renders and those years are shown as gaps (or points omitted), not as zero.
  - If the user inserts only a year (no country), then the system displays an informative message like "please enter a country to view a trend" (no chart).
  - If the user inserts an invalid country, outputs string "invalid year or country".

## Feature 3: Search bar - Shows the ranking of a country's CO2 emmission relative to deforestation rate in a certain year (2000-2025)
* Person responsible: Simon
* User story: As a general person interested in sustainability related topics, I can look up a country and year and see how that country ranks on a CO2-to-deforestation metric compared to other countries in that year, allowing me to catch a glimpse on how big is deforestation contributing to the influence on the environment.
* Acceptance Criteria:
  - Given the user is on the CO2-vs-deforestation ranking page, when the user selects a valid country and a valid year, then the system displays the country’s rank for that year based on CO2 emission relative to deforestation rate (e.g., a computed ratio like CO2 / deforestation_rate), and shows the underlying values used (CO2, deforestation rate, and the computed metric).
  - If the user inserts only a year, then the system displays a ranked list for all countries in that year based on the chosen metric (highest to lowest), with ranks shown.
  - If the user inserts only a country, then the system displays the country’s ranking for the most recent year available (and shows which year was used).
  - If the deforestation rate is 0 or missing for a country-year, then the system does not divide by zero; instead it displays "insufficient data" for that country-year (and excludes it from the ranked list).
  - If the user inserts an invalid year or an invalid country, outputs string "invalid year or country".


# Datasets Metadata
Deforestation and Forest Loss
https://ourworldindata.org/deforestation
Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World in Data. “Annual change in forest area” [dataset]. Food and Agriculture Organization of the United Nations, “Global Forest Resources Assessment 2025” [original data].
Source: Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World In Data
https://ourworldindata.org/grapher/deforestation-share-forest-area.csv
(accessed on Jan 10, 2026)
 


CO2 Emissions per Capita
Citation
Global Carbon Budget (2025); Population based on various sources (2024) – with major processing by Our World in Data. “CO₂ emissions per capita” [dataset]. Global Carbon Project, “Global Carbon Budget v15”; Various sources, “Population” [original data]. Retrieved January 10, 2026 from https://archive.ourworldindata.org/20251204-133459/grapher/co-emissions-per-capita.html  (archived on December 4, 2025).


CO2 and Greenhouse Gas Emissions 
https://ourworldindata.org/co2-and-greenhouse-gas-emissions
Hannah Ritchie, Pablo Rosado, and Max Roser (2023) - “CO₂ and Greenhouse Gas Emissions” Published online at OurWorldinData.org. Retrieved January 13, 2026 from: 'https://ourworldindata.org/co2-and-greenhouse-gas-emissions' [Online Resource]



Share of land covered by forest
https://ourworldindata.org/grapher/forest-area-as-share-of-land-area
Various sources – with major processing by Our World in Data. “Share of land covered by forest” [dataset]. Our World in Data.
Source: Department for Environment, Food & Rural Affairs (2013); Food and Agriculture Organization of the United Nations (2025); Forest Research (2002); Mather A.S., Fairbairn J., & Needle C.J. (1999); Osamu Saito (2009); Yi-Ying Chen et al. (2019); A.S. Mather (2008); Kleinn, Corrales & Morales (2002); Soo Bae J., Won Joo R., & Kim Y.S. (2012); United States Department of Agriculture, Forest Service (2014); He, F., Yang & Wang (2024); Scottish Government (2019); FAO via World Bank (2025).
(accessed on Jan 17, 2026)

# Mock up
![webpage layout](https://github.com/user-attachments/assets/d1268496-a329-48c2-82a1-5ae3b78f95c3)

# Data story
  We chose deforestation because forest loss is directly related to biodiversity and climate impacts (SDG 15 +13), and this was both mentioned of interest by Simon and Amery. We chose CO₂ per capita because it is a widely used way to compare emissions responsibilities across countries. We are excited because combining these datasets would build a comparison tool to explore whether high-emitting countries also show high deforestation rates. 
