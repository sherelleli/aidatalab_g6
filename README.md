# AI.Data Lab Fall 2025 - Impact of FIFA World Cup on Atlanta Businesses
## The Problem
We want to help business owners in the Atlanta area understand the projected foot traffic and gague its impact on their own business in order to accomodate the uptick.

## Our Approach + Scope
We wanted to know, based on ridership and business patterns from past major events, which Atlanta businesses are likely to see the largest increase in public transit use and potential customer traffic during the World Cup.

We used our findings to create an LLM trained on our findings for business owners to query to provide specific impact data for their situation.

### Our Data
1. Business license data from the City of Atlanta
2. Bus and Train MARTA Ridership data from the past two years (1/1/23 to 8/31/25). Bus data is organized by Route, Train data is organized by Station.
3. Using external data: We made a meta-dataset (atlanta_sports.csv) by identifying major sports events from the past two years (such as Falcons, Atlanta United, or SEC Championship games)

### Our Goals
1. To link our meta-dataset to corresponding changes in ridership and nearby business patterns.
2. Link ridership change to business characteristics
– Examine whether neighborhoods with higher concentrations of restaurants, hotels, or retail stores show larger ridership surges.
– Use correlation or regression analysis to test how business density and type predict ridership spikes.
3. Model the World Cup Impact based upon these predictions.

## Our Deliverable
The model is available here: __LINK HERE__



## Our Research Methods
Our research unfolded in two different tracks of analyses:
### 1. Bus + Train Ridership Analysis
We began by comparing the baseline or non-sporting event weekends to those that similarly-sized events at the Benz took place in.

We plotted each train station to see where in Atlanta is most popular for these weeks compared to non-event weeks.
**ADD A HEAT MAP HERE PLEASE**
Can do for both bus and train ridership_
add a graph where you rank by station^^


### 2. Business Licensing Analysis

Created Spatial Map of the Businesses
# References/Appreciation
Many thanks to Invest Atlanta for providing this data and in investing in our project's success.
THANK THE MAJOR PROFS AND PEOPLE THAT HELPED ON TUESDAY NIGHTS.