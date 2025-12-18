"""validate_json_schema tool - JSON schema validator (TalkAPI by RAJ)"""

import json
from typing import Any, Dict
from mcp.types import Tool
from jsonschema import validate, ValidationError, Draft202012Validator


class ValidateJSONSchemaTool:
    """Tool for validating JSON against a schema"""
    
    def get_definition(self) -> Tool:
        """Return tool definition for MCP"""
        return Tool(
            name="validate_json_schema",
            description=(
                "Validate JSON data against a JSON Schema. "
                "Returns detailed validation errors if the data doesn't match the schema. "
                "This allows the LLM to act as strict QA, identifying type mismatches, "
                "missing required fields, or format violations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": ["object", "array"],
                        "description": "JSON data to validate (as structured object)",
                    },
                    "schema": {
                        "type": "object",
                        "description": "JSON Schema definition (as structured object)",
                    },
                },
                "required": ["data", "schema"],
            },
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Validate JSON against schema"""
        data = arguments.get("data")
        schema = arguments.get("schema")
        
        if not schema:
            return json.dumps({
                "valid": False,
                "error": "Schema is required",
            }, indent=2)
        
        try:
            # Validate schema itself first
            Draft202012Validator.check_schema(schema)
            
            # Validate data against schema
            validate(instance=data, schema=schema)
            
            return json.dumps({
                "valid": True,
                "message": "✅ Data matches schema",
            }, indent=2)
        
        except ValidationError as e:
            # Extract detailed error information
            error_path = ".".join(str(p) for p in e.path) if e.path else "root"
            
            result = {
                "valid": False,
                "message": "❌ Validation failed",
                "error": {
                    "path": error_path,
                    "message": e.message,
                    "validator": e.validator,
                },
            }
            
            # Add context if available
            if e.validator_value is not None:
                result["error"]["expected"] = e.validator_value
            
            if e.instance is not None:
                result["error"]["actual"] = e.instance
            
            return json.dumps(result, indent=2, default=str)
        
        except Exception as e:
            return json.dumps({
                "valid": False,
                "error": f"Schema validation error: {str(e)}",
            }, indent=2)

