# How the Catalonia wildfire data was cleaned

**[CleanData.csv](CleanData.csv) is the combined file for analysis.** It contains 16,470 fire records. The project starts with Spanish government reports (GovEsp) and uses Generalitat de Catalunya records (GenCat) to fill gaps in coverage. The `font` column tells you which source supplied each row.

| Step | Notebook | Output | Rows |
| --- | --- | --- | ---: |
| 1. Clean the Spanish government reports | [GovEsp preprocessing](../GovEsp%20preprocessing.ipynb) | [CleanGovEsp.csv](CleanGovEsp.csv) | 15,366 |
| 2. Clean the Generalitat records | [GenCat preprocessing](../GenCat%20preprocessing.ipynb) | [Clean GenCat Data.csv](Clean%20GenCat%20Data.csv) | 7,448 |
| 3. Combine the two sources | [Merge csvs](../Merge%20csvs.ipynb) | [CleanData.csv](CleanData.csv) | 16,470 |

To rebuild the files, run the two preprocessing notebooks from the project root in either order, then run the merge notebook. They read the raw files and reference tables from `dades/`.

## 1. GovEsp — assemble each fire report

The raw file, `Xml_20261119_124136_1.xml`, stores a report’s location, cause, detection time and burned area in separate sections. The notebook brings them together using the report number, `numeroparte`.

- **Location.** The notebook combines the two-digit province code and three-digit local municipality code. A local code of zero means the municipality is unknown. It looks up municipality and province names in `MUNICIPIOS.csv` and the comarca (county) in `corrMpisComsAtps.csv`. Where latitude or longitude is missing, it fills that value with the municipality reference coordinate if available. The flag `coords_imputades` records whether the original latitude was missing and a municipality code was available.
- **Cause.** The notebook looks up the cause code in `causes_egif_ca.csv`. It keeps the code and leaves the description blank when the label is *Desconeguda* (unknown).
- **Date.** The notebook keeps the calendar date of detection and drops the time of day. An unreadable date becomes blank.
- **Burned area.** The notebook adds the reported hectares of wooded forest, non-wooded forest, agricultural land and other non-forest land. If some components are missing, the total covers only the recorded components. If all four are missing, the total stays blank.

A report needs a matching location, cause record and time record to enter the GovEsp export. A missing area record does not remove it. The exported CSV includes a leading row index, which the merge later discards. It also omits the comarca name looked up during preprocessing.

## 2. GenCat — clean the incident list

The raw file, `Incendis_forestals_a_Catalunya._Anys_2011-2024_20261116.csv`, contains 7,545 rows for 2011–2024. It provides a date and municipality for each fire. The notebook assigns each row a project ID based on its original position because the source has no official incident ID.

1. **Remove exact repeats.** The notebook compares all nine original fields, including burned area. It keeps the first copy and removes 97 repeated rows, leaving 7,448. The surviving rows keep their original IDs, so gaps are expected. Two records on the same day in the same town both survive if any source field differs. Identical reports could still describe separate fires, so this is a cleaning assumption.
2. **Check the area values.** The notebook reads European number formatting correctly (`5.621,80` means 5,621.80 hectares) and checks the forest total against its components. It retains the 1,360 source rows with four zero areas during this check. It also keeps the Mollet del Vallès record of 4 October 2018, whose non-wooded forest area is missing. Its date and location are usable.
3. **Look up the location.** The notebook removes the last digit (a check digit) from the six-digit municipality code. It uses the remaining five digits to look up names and comarca in `corrMpisComsAtps.csv` and coordinates in `MUNICIPIOS.csv`. Every GenCat coordinate represents the municipality. The source does not give an exact fire location.
4. **Export dates and locations.** Dates change from day/month/year to year-month-day. The notebook checks that the lookups preserved the row count, that IDs are unique and that all exported date and location fields are filled. The intermediate CSV stores the province and local municipality codes separately. It leaves out the raw area columns, so GenCat rows have blank hectares in the combined file.

## 3. Merge — decide which records to keep

The merge removes the intermediate row indexes, aligns the column names and converts coordinates with decimal commas to numbers. It restores two-digit province codes and full five-digit municipality codes, including leading zeroes. IDs gain a source prefix such as `GovEsp:` or `GenCat:` so they stay unique.

**GovEsp takes priority for each municipality and calendar day.** The merge uses the municipality code to find a common spelling of the town name where possible, then ignores case and extra spaces when comparing names. The exported row keeps its source spelling. A missing name cannot match.

For example, if GenCat lists two fires in one town on a day when GovEsp lists one, the combined file keeps the one GovEsp report. If GovEsp lists none there that day, both GenCat records are added. This rule checks coverage by place and day. It cannot establish that two individual reports describe the same fire.

Of the 7,448 GenCat records, 6,343 matched a GovEsp municipality and day. The merge added the remaining **1,105**. Of those, 60 fell within the shared coverage years (2011–2022) and 1,045 came from 2023–2024.

**One fire crossed a provincial boundary.** On 18 July 1998, the Aguilar de Segarra fire generated separate Barcelona and Lleida reports. The merge adds their areas to **17,675.18 hectares** and keeps the origin record, `GovEsp:1998080173`. Both original reports remain in the GovEsp CSV. The Cardona fire on 19 July remains a separate incident. [MITECO wildfire report, tables 17 and 19](https://miteco.gob.es/content/dam/miteco/es/biodiversidad/temas/incendios-forestales/decenio_1996_2005_tcm30-132558.pdf)

The final count is **15,366 GovEsp reports + 1,105 GenCat additions − 1 consolidated report = 16,470 rows**. The file is sorted by date and then by incident ID.

## Reading the combined file

- **For maps**, read `codi_provincia`, `codi_municipi` and `codi_comarca` as text to preserve leading zeroes. The merge assigns comarca codes using the project’s 2024 geography, including for older fires. Fourteen rows have no matching comarca code and are retained. GovEsp rows can have a comarca code even though their comarca name is blank.
- **For coordinates**, check `font` alongside `coordenades_imputades`. The flag comes from GovEsp’s latitude check. GenCat leaves it blank even though all its coordinates are municipality reference points.
- **For causes and hectares**, only GovEsp contributes values to the final file. A blank `total_hectares` means the combined file has no area value for that record. Treating it as zero would distort averages.
