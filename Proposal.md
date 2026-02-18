# Team D - Carbon & Forests Dashboard: Deforestation and CO₂ Emissions

# Sustainable Development Goal(s): Goal 13: Climate action & Goal 15: Life on land

* This project will facilitate the exploration and comparison of territorial CO₂ emissions and deforestation across countries and over time. By turning these datasets into searchable country pages, rankings, cross-dataset comparisons, users can identify trends, supporting education and more informed conversations about climate mitigation and forest conservation.
* Hopefully this will also help people realize the harm of deforestation and take actions to contribute to the protection of trees, since CO2 concentration rise has a direct negative impact on human, and the Earth as a whole.

# Features

## Feature 1: Deforestation rate - Given a certain country and year; returns the deforestation rate of that country in the specific year.
* Person responsible: Milly
* User story: As a general person interested in sustainability related topics, I can look up a country and year and see the deforestation rate of that country in that year.
* Acceptance Criteria:
  - Given the user is on the deforestation lookup page, when the user selects Algeria and 2020, the system will display "Deforestation area of Algeria in 2020 is -673.999 ha"
  - Given the user is on the deforestation lookup page, when the user selects Algeria, the system will display "please select a valid country or year".
  - Given the user is on the deforestation lookup page, when the user selects 2020, the system will display "please select a valid country or year".
  - Given the user is on the deforestation lookup page, when the user selects Germany and 2020, the system will display "Deforestation area of Germany in 2020 is 0.027929546 ha".
  
## Feature 2: CO2 emission — Given a certain country and year; returns the CO2 emission (per capita) of that country in the specific year.
* Person responsible: Simon
* User story: As a general person interested in sustainability-related topics, I can look up a country and year and see the CO₂ emissions per capita of that country in that year.
* Acceptance Criteria: 
  - Given the user is on the CO₂ lookup page, when the user selects Algeria and 2020, the system will display "CO₂ emissions per capita of Algeria in 2020 is 3.8857946".
  - Given the user is on the CO₂ lookup page, when the user selects Algeria (but no year), the system will display "please select a valid country or year".
  - Given the user is on the CO₂ lookup page, when the user selects 2020 (but no country), the system will display "please select a valid country or year".
  - Given the user is on the CO₂ lookup page, when the user selects Germany and 2020, the system will display "CO₂ emissions per capita of Germany in 2020 is 7.738692".

## Feature 3: Ranking - Given a specific country and year; returns the ranking of deforestation and CO2 emission of that country in the specific year.
* Person responsible: Amery
* User story: As a general person interested in sustainability-related topics, I can look up a country and year and see how that country ranks (relative to other countries) in deforestation and CO₂ emissions per capita for that year.
* Acceptance Criteria:
  - Given the user is on the ranking page, when the user selects Germany and 2020, the system will display "In 2020, Germany ranks #77 in deforestation and #41 in CO₂ emissions per capita."
  - Given the user is on the ranking page, when the user selects Algeria and 2020, the system will display "In 2020, Algeria ranks #32 in deforestation and #102 in CO₂ emissions per capita."
  - Given the user is on the ranking page, when the user selects Algeria (but no year), the system will display "please select a valid country or year".
  - Given the user is on the ranking page, when the user selects 2020 (but no country), the system will display "please select a valid country or year".


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
