# 📂 MOFA RAW Feeds

This directory contains raw output information related to Microsoft Standalone Applications and Mac/iOS App Store applications. These outputs are generated automatically using scripts, providing MacAdmins with the latest information in various formats. This setup simplifies the process of accessing and managing app-related data provided by Microsoft.

## 🛠️ Repository Overview

- **Scripts Location**: All scripts used to retrieve and process the data are located in the `/.github/actions/` directory of the repository. These scripts automate the fetching and formatting of app data from Microsoft-provided feeds. The raw data is automatically updated every 1 hour using a GitHub Action, which is triggered by workflows located in the `/.github/workflows/` directory.
  - **Purpose**: The scripts collect app metadata, convert it into multiple formats, and ensure the information remains current.

## 📄 File Outputs

This directory contains the following types of output files:

1. 🧩 **XML Files**
   - **Description**: These files provide app information in XML format, suitable for systems and applications requiring structured data.
   - **Use Case**: XML is widely used for data exchange and is ideal for environments requiring standardized, hierarchical data representation.

2. 🌐 **JSON Files**
   - **Description**: App information is also provided in JSON format, which is lightweight and easy to parse.
   - **Use Case**: JSON is commonly used in modern web applications and APIs due to its simplicity and flexibility.

3. ✍️ **YAML Files**
   - **Description**: YAML files offer a human-readable way of representing app data.
   - **Use Case**: YAML is particularly useful for configuration files and scenarios where readability and simplicity are prioritized.

## 🌟 Why Provide Multiple Formats?

The choice to provide XML, JSON, and YAML outputs ensures compatibility with a wide range of tools and systems. By supporting multiple formats, we accommodate diverse user needs:

- **XML**: Designed for enterprise applications and legacy systems.
- **JSON**: Suitable for modern development environments and APIs.
- **YAML**: Ideal for user-friendly configuration and quick manual edits.

## 📌 Usage Instructions

1. Locate the required output file in this directory.
2. Refer to the scripts in the `/.github/actions/` directory to understand or customize how the data is fetched and formatted.
3. Choose the format that best fits your application or integration needs.

