# Real Data Import Guide

This document outlines the expected CSV file formats for bulk-importing catalogue data (destinations, locations, hotels, activities, transport modes) using the `import_from_csv.py` script.

**Usage:**

```bash
python import_from_csv.py <entity_type> <path_to_csv_file>
```

-   `<entity_type>`: One of `destinations`, `locations`, `hotels`, `activities`, `transport_modes`.
-   `<path_to_csv_file>`: The path to the corresponding CSV file.

The script uses an "upsert" strategy: it will insert new records or update existing ones based on unique identifiers (usually `name` or `code`).

---

## CSV Formats

All CSV files should use UTF-8 encoding and have a header row matching the columns specified below.

### 1. Destinations (`destinations`)

| Column      | Type    | Description                                  | Example        | Required | Unique Key |
| :---------- | :------ | :------------------------------------------- | :------------- | :------- | :--------- |
| `name`      | String  | Unique name of the destination.              | Phuket         | Yes      | Yes        |
| `latitude`  | Float   | Latitude coordinate.                         | 7.9519         | Yes      |            |
| `longitude` | Float   | Longitude coordinate.                        | 98.3364        | Yes      |            |

### 2. Locations (`locations`)

| Column           | Type   | Description                                                                 | Example                     | Required | Unique Key (Assumed) |
| :--------------- | :----- | :-------------------------------------------------------------------------- | :-------------------------- | :------- | :------------------- |
| `destination_name` | String | Name of the parent Destination (must match an existing Destination `name`). | Phuket                      | Yes      |                      |
| `name`           | String | Name of the location (e.g., area, airport, pier).                           | Patong Beach Area           | Yes      | Yes                  |
| `kind`           | String | Type of location (e.g., `Airport`, `HotelArea`, `AttractionSite`, `Pier`).  | HotelArea                   | Yes      |                      |

*Note: The script currently assumes `name` is globally unique for locations during upsert. A more robust implementation might use a composite key (destination_name, name).*

### 3. Hotels (`hotels`)

| Column         | Type   | Description                                                               | Example                                           | Required | Unique Key (Assumed) |
| :------------- | :----- | :------------------------------------------------------------------------ | :------------------------------------------------ | :------- | :------------------- |
| `location_name`| String | Name of the parent Location (must match an existing Location `name`).     | Patong Beach Area                                 | Yes      |                      |
| `name`         | String | Name of the hotel.                                                        | Grand Mercure Patong                              | Yes      | Yes                  |
| `amenities_json`| String | JSON string representing hotel amenities. Keys/values are flexible.       | `{"pool": true, "rating": 5, "restaurant": true}` | No       |                      |

*Note: The script currently assumes `name` is globally unique for hotels during upsert.*

### 4. Activities (`activities`)

| Column        | Type   | Description                                                               | Example                   | Required | Unique Key (Assumed) |
| :------------ | :----- | :------------------------------------------------------------------------ | :------------------------ | :------- | :------------------- |
| `location_name`| String | Name of the parent Location (must match an existing Location `name`).     | Rassada Pier              | Yes      |                      |
| `name`        | String | Name of the activity.                                                     | Phi Phi Islands Day Tour  | Yes      | Yes                  |
| `category`    | String | Category of the activity (e.g., `Adventure`, `Relaxation`, `Culture`).    | Adventure                 | No       |                      |
| `price_min`   | Float  | Estimated minimum price (use 0 if free, leave blank if unknown).          | 1500                      | No       |                      |
| `price_max`   | Float  | Estimated maximum price (can be same as min, leave blank if unknown).     | 2500                      | No       |                      |

*Note: The script currently assumes `name` is globally unique for activities during upsert.*

### 5. Transport Modes (`transport_modes`)

| Column | Type   | Description                                                                                                | Example     | Required | Unique Key |
| :----- | :----- | :--------------------------------------------------------------------------------------------------------- | :---------- | :------- | :--------- |
| `code` | String | Unique code matching the `TransportModeEnum` values (`flight`, `ferry`, `bus`, `taxi`, `private_car`, `minivan`). | ferry       | Yes      | Yes        |
| `name` | String | Display name for the transport mode.                                                                       | Speedboat Ferry | Yes      |            |

---

**Notes:**

*   The import script uses entity names (e.g., `destination_name`, `location_name`) to look up foreign keys. Ensure these names exactly match existing records in the database *before* running the import for dependent entities.
*   Run imports in order: `destinations` -> `locations` -> `hotels`, `activities`, `transport_modes`.
*   Error handling is basic. Malformed CSVs or data inconsistencies might cause rows to be skipped or the import to fail. Check the script logs for details.
*   For large files, consider adding batching logic to the import script.
