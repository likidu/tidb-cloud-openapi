#!/usr/bin/env python3

import json
import yaml
import glob
from pathlib import Path

def load_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def save_yaml_file(data, file_path):
    with open(file_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

def combine_specs():
    # Initialize the combined spec
    combined_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "TiDB Cloud Serverless Open API",
            "description": "TiDB Cloud Serverless Open API",
            "version": "v1beta1"
        },
        "servers": [
            {
                "url": "https://serverless.tidbapi.com/v1beta1",
                "description": "TiDB Cloud Serverless API server"
            }
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [{"BearerAuth": []}]
    }

    # Get all swagger files
    swagger_files = glob.glob("*.swagger.json")
    
    for file_path in swagger_files:
        spec = load_json_file(file_path)
        
        # Convert paths from Swagger 2.0 to OpenAPI 3.0
        for path, path_item in spec.get("paths", {}).items():
            if path not in combined_spec["paths"]:
                combined_spec["paths"][path] = {}
            
            for method, operation in path_item.items():
                # Convert parameters
                parameters = []
                for param in operation.get("parameters", []):
                    if param.get("in") == "body":
                        # Convert body parameter to requestBody
                        operation["requestBody"] = {
                            "content": {
                                "application/json": {
                                    "schema": param["schema"]
                                }
                            }
                        }
                        if param.get("required"):
                            operation["requestBody"]["required"] = True
                    else:
                        # Convert other parameters
                        oas3_param = {
                            "name": param["name"],
                            "in": param["in"],
                            "description": param.get("description", ""),
                            "required": param.get("required", False)
                        }
                        if "type" in param:
                            oas3_param["schema"] = {"type": param["type"]}
                            if "format" in param:
                                oas3_param["schema"]["format"] = param["format"]
                        if "enum" in param:
                            oas3_param["schema"]["enum"] = param["enum"]
                        parameters.append(oas3_param)
                
                # Convert responses
                responses = {}
                for status, response in operation.get("responses", {}).items():
                    oas3_response = {
                        "description": response.get("description", "")
                    }
                    if "schema" in response:
                        oas3_response["content"] = {
                            "application/json": {
                                "schema": response["schema"]
                            }
                        }
                    responses[status] = oas3_response
                
                # Update the operation
                operation["parameters"] = parameters
                operation["responses"] = responses
                combined_spec["paths"][path][method] = operation
        
        # Add schemas
        for name, schema in spec.get("definitions", {}).items():
            combined_spec["components"]["schemas"][name] = schema

    # Save the combined spec
    save_yaml_file(combined_spec, "openapi.yaml")

if __name__ == "__main__":
    combine_specs() 