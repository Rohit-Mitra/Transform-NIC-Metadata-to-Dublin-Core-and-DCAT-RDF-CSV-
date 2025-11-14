# Transform-NIC-Metadata-to-Dublin-Core-and-DCAT-RDF-CSV-

# NIC Metadata to Dublin Core and DCAT Converter

## Overview

This Python script converts metadata from the NIC format (assignment.csv) into two standard metadata formats:
- **Dublin Core (DC)**: A simple standard for describing datasets at a general level
- **DCAT (Data Catalog Vocabulary)**: A more detailed W3C standard that includes dataset descriptions and distribution information

## Installation

### Prerequisites
- Python 3.7 or higher
- Required libraries:

```bash
pip install pandas rdflib
```

## Usage

1. Place `assignment.csv` in the same directory as the script
2. Run the script:

```bash
python metadata_converter.py
```

3. Check the `output/` directory for generated files:
   - `dublin.ttl` - Dublin Core metadata in RDF Turtle format
   - `dublin.csv` - Dublin Core metadata in CSV format
   - `dcat.ttl` - DCAT metadata in RDF Turtle format
   - `dcat.csv` - DCAT metadata in CSV format

## Implementation Details

### Dublin Core Mapping

The following fields from assignment.csv are mapped to Dublin Core terms:

| CSV Field | Dublin Core Term | Notes |
|-----------|-----------------|-------|
| title | dct:title | Direct mapping |
| catalog_title + note | dct:description | Combined for detailed description |
| published_date | dct:issued | Parsed to ISO 8601 date format |
| changed | dct:modified | Parsed to ISO 8601 date format |
| created | dct:created | Parsed to ISO 8601 date format |
| ministry_department or state_department | dct:publisher | Uses ministry_department first, falls back to state_department |
| frequency | dct:accrualPeriodicity | Normalized to standard frequency URIs |
| sector | dct:subject | Split on semicolons for multiple subjects |
| node_alias | dcat:landingPage | Constructed as https://data.gov.in{node_alias} |

### DCAT Mapping

DCAT extends Dublin Core with additional dataset and distribution information:

**Dataset Level:**
- All Dublin Core mappings above
- sector → dcat:theme (for dataset themes)
- Each dataset is typed as dcat:Dataset

**Distribution Level:**
- API Distribution (when datafile_url exists):
  - datafile_url → dcat:accessURL
  - file_format → dct:format and dcat:mediaType
  - file_size → dcat:byteSize (as integer)
  
- File Distribution (when datafile exists):
  - datafile → dcat:downloadURL
  - file_format → dct:format and dcat:mediaType
  - file_size → dcat:byteSize (as integer)

### Frequency Normalization

The script normalizes frequency terms to standard vocabulary:
- daily → http://purl.org/cld/freq/daily
- weekly → http://purl.org/cld/freq/weekly
- monthly → http://purl.org/cld/freq/monthly
- quarterly → http://purl.org/cld/freq/quarterly
- yearly → http://purl.org/cld/freq/annual

## Assumptions Made

1. **Date Parsing**: The script attempts to parse dates in multiple formats (d/m/Y, Y-m-d, m/d/Y). If parsing fails, it uses the original string value.

2. **Publisher Priority**: When both ministry_department and state_department are present, ministry_department is used as the publisher.

3. **Description Construction**: The description is constructed by combining catalog_title and note fields. If only one is available, that field is used.

4. **URI Construction**: Dataset URIs are constructed using the node_alias field. If node_alias is missing, a generic URI with the row index is used.

5. **Distribution Types**: The script creates separate distributions for API access (datafile_url) and file downloads (datafile). If both are present, the dataset will have two distributions.

6. **MIME Types**: The file_format field is used directly as the media type. In production, this should be validated against standard MIME types.

## Unmapped Fields

The following fields from assignment.csv could not be directly mapped to Dublin Core or DCAT standards:

| Field Name | Reason for Non-Mapping |
|------------|------------------------|
| resource_category | No direct equivalent in DC/DCAT; could potentially be used as dcat:theme |
| govt_type | No standard property; could be added as custom property if needed |
| sector_resource | Redundant with sector field |
| field_resource_type | Internal classification; no standard mapping |
| granularity | Could be mapped to dcat:granularity in DCAT v3, but not implemented |
| field_from_api | Technical metadata; no standard mapping |
| is_api_available | Implied by presence of API distribution |
| is_visualized | Application-specific metadata |
| api_request_count | Usage statistics; no standard mapping |
| field_high_value_dataset | Could be a custom property or dcat:qualifiedRelation |
| field_show_export | UI-specific metadata |
| cdos_state_ministry | Organizational metadata; covered by publisher |
| is_rated | Quality metadata; no direct mapping |
| external_api_reference | Could be related entity, but no clear mapping |
| ogdp_download_count | Usage statistics; no standard mapping |
| ogdp_view_count | Usage statistics; no standard mapping |
| domain | Could be part of spatial or theme, but ambiguous |

### Potential Extensions

Some unmapped fields could be included using DCAT v3 extensions:
- Usage statistics (download_count, view_count) → dcat:DatasetSeries or custom properties
- Quality indicators (is_rated) → dcat:qualifiedRelation with dqv:QualityAnnotation
- High value dataset flag → custom property or dcat:qualifiedRelation

## Output Structure

### CSV Outputs

**dublin.csv**: One row per dataset with columns:
- dataset_uri, title, description, issued, modified, created, publisher, accrualPeriodicity, subject, landingPage

**dcat.csv**: One row per distribution with columns:
- dataset_uri, distribution_uri, distribution_type, accessURL, downloadURL, format, byteSize, title

### RDF Outputs

Both Turtle files contain valid RDF triples using standard namespaces:
- dcterms: http://purl.org/dc/terms/
- dcat: http://www.w3.org/ns/dcat#
- xsd: http://www.w3.org/2001/XMLSchema#

## Validation

The script includes basic error handling for:
- Missing input file
- Date parsing errors
- Invalid numeric values for file_size
- Missing required fields

## References

- Dublin Core Metadata Initiative: https://www.dublincore.org/
- DCAT Version 3: https://www.w3.org/TR/vocab-dcat-3/
- RDFLib Documentation: https://rdflib.readthedocs.io/

## Author

Created for NIC Data Analyst Fellow Assignment

## License

This script is provided as-is for the assignment evaluation.
