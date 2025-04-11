# Material Master Data MCP

**Version:** 1.0.1  
**Author:** ORBIS Consulting Shanghai Co.,Ltd  
**License:** MIT  
**Last Updated:** April 11, 2025  
**Limitation:** This function is only for demonstration, cannot use in a productive environment. If you need, please contact the author: ruiyang.shen@orbis.de

Material Master Data MCP (Master Control Program) is a service for interacting with SAP systems to provide master data query functionality. The service can run as an HTTP API server or as a tool in standard input/output mode, supporting integration with smart assistants like Cursor.

## Features

- **Dual Mode Operation**: Supports both HTTP API and standard input/output (stdio) modes
- **Material Basic Information Query**: Retrieves detailed attributes and characteristics of materials
- **Material Description Search**: Finds relevant materials based on description text
- **Multilingual Support**: Supports querying material descriptions in different languages (Chinese, English, German, etc.)
- **Type Safety**: Uses Pydantic models for input validation
- **Complete API Documentation**: Built-in API documentation using OpenAPI specification
- **MCP.so Hosting Support**: Can be deployed to MCP.so for cloud-based access
- **API Key Authentication**: Uses JWT for secure authentication

## Installation

### Requirements

- Python 3.7+
- Access to a SAP S/4HANA system

### Installation Steps

1. Clone this repository:

```bash
git clone https://github.com/SHENRUIYANG/S4MCPDEMO.git
cd S4MCPDEMO
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure SAP connection (optional, can also use environment variables):

Create a `.env` file in the project root directory with the following content:

```
SAP_HOST=your_sap_host
SAP_PORT=your_sap_port
SAP_USER=your_sap_username
SAP_PASSWORD=your_sap_password
JWT_SECRET=your-secret-key  # 用于生成和验证 API Key 的密钥
```

4. Generate API Key:

For security reasons, the API key generation script is not included in the public repository. If you need to generate API keys for this service, please contact the author directly.

API keys use JWT format and include:
- User email
- SAP connection information (host, port, username, password)
- Expiration date

**Note**: API keys contain sensitive connection information and should be kept secure.

## Usage

### Start as HTTP Server

```bash
python MM03_MCP.py --mode=http --host=0.0.0.0 --port=5003
```

This will start a FastAPI server, listening on the specified port (default 5003).

### Start as Standard Input/Output (stdio) Tool

```bash
python MM03_MCP.py --mode=stdio
```

This will start the program and wait for commands on standard input, suitable for integration with smart assistants like Cursor.

### Start as REST Server (for MCP.so)

```bash
python MM03_MCP.py --mode=rest --host=0.0.0.0 --port=5003 --endpoint=/rest
```

This will start a REST server suitable for MCP.so hosting.

### API Endpoints

After starting the HTTP server, the following API endpoints are available:

- **GET /.well-known/mcp-manifest.json**: Get API manifest
- **POST /mcp_MM03_BasicData**: Get material basic information
- **POST /mcp_MM03_DescToMaterial**: Search materials by description
- **POST /mcp_MM03_Description_Search**: Get material descriptions in specific languages
- **GET /health**: Health check endpoint

### API Documentation

After starting the HTTP server, you can view the complete API documentation by visiting `http://localhost:5003/docs`.

## Example Usage

### Get Material Basic Information

```bash
curl -X POST "http://localhost:5003/mcp_MM03_BasicData" \
  -H "Content-Type: application/json" \
  -d '{"material": "FG126"}' \
  -H "Authorization: Bearer your-api-key"
```

### Search Materials by Description

```bash
curl -X POST "http://localhost:5003/mcp_MM03_DescToMaterial" \
  -H "Content-Type: application/json" \
  -d '{"description": "serial", "language": "EN"}' \
  -H "Authorization: Bearer your-api-key"
```

### Get Material Description in a Specific Language

```bash
curl -X POST "http://localhost:5003/mcp_MM03_Description_Search" \
  -H "Content-Type: application/json" \
  -d '{"material": "FG126", "language": "EN"}' \
  -H "Authorization: Bearer your-api-key"
```

## MCP.so Integration

This project is designed to be compatible with MCP.so hosting. The repository includes all necessary files:

- **chatmcp.yaml**: Configuration for MCP.so integration
- **Dockerfile**: Container image definition for deployment
- **LICENSE**: MIT license as required for commercial-friendly deployment

To deploy this service to MCP.so:
1. Submit the GitHub repository URL to the MCP.so platform
2. The service will be reviewed and deployed by the MCP.so team
3. Once approved, it will be available for use in the MCP Playground

## Docker Deployment

You can also run the service in a Docker container:

```bash
# Build the Docker image
docker build -t mcp/mm03-mcp .

# Run the container
docker run -i --rm -e SAP_USER=your_username -e SAP_PASSWORD=your_password mcp/mm03-mcp
```

## API Details

### BasicData

Get basic information for a material.

**Input Parameters:**
- `material`: Material number (e.g., "FG126")

**Return Fields:**
- Material type (ProductType)
- Creation date (CreationDate)
- Gross weight (GrossWeight)
- Base unit of measure (BaseUnit)
- Material group (ProductGroup)
- And many more SAP material master data fields

### DescToMaterial

Search materials by description text.

**Input Parameters:**
- `description`: Description text (e.g., "valve")
- `max_results`: Maximum number of results (default: 50)
- `language`: Language code (e.g., "EN" for English, "ZH" for Chinese, "ALL" for all languages, default is "ZH")

**Return Fields:**
- `material`: Material number
- `description`: Material description
- `language`: Language code

### Description_Search

Get description information for a specific material in a specified language.

**Input Parameters:**
- `material`: Material number (e.g., "FG126")
- `language`: Language code (e.g., "EN" for English, "ZH" for Chinese, default is "EN")

**Return Fields:**
- `material`: Material number
- `description`: Material description
- `language`: Language code

## Dependencies

- FastAPI: Web framework
- Uvicorn: ASGI server
- httpx: Asynchronous HTTP client
- python-dotenv: Environment variable management
- Pydantic: Data validation
- FastMCP: MCP core library

## Security Considerations

- In production environments, it is recommended to enable HTTPS
- Do not hardcode credentials in code; use environment variables or secure credential management solutions
- Ensure that only authorized users can access the API

## License

[MIT License](LICENSE)

## Contributing

Issues and pull requests are welcome! 