from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timezone

load_dotenv(override=True)
mcp = FastMCP("agromarket_server")
# mcp = Server("agromarket_server")

@mcp.resource("config://app-version")
def get_app_version() -> dict:
    """Static resource providing application version information"""
    return {
        "name": "agromarket_server",
        "version": "1.0.0",
        "release_date": "2025-10-15",
        "environment": "production"
    }

# Example 2: Dynamic Resource with URI Template - Crop Disease Data
@mcp.resource("disease://crop/{crop_type}/list")
async def get_diseases_by_crop(crop_type: str)-> dict:
    """
    Dynamic resource that provides list of diseases for a specific crop type
    URI: disease://crop/wheat/list
    """
    # This is read-only - just fetching and returning data
    disease_database = {
        "wheat": [
            {"name": "Wheat Rust", "severity": "high"},
            {"name": "Powdery Mildew", "severity": "moderate"}
        ],
        "rice": [
            {"name": "Rice Blast", "severity": "high"},
            {"name": "Bacterial Blight", "severity": "moderate"}
        ],
        "corn": [
            {"name": "Corn Smut", "severity": "moderate"},
            {"name": "Northern Corn Leaf Blight", "severity": "high"}
        ]
    }
    
    return {
        "crop_type": crop_type,
        "diseases": disease_database.get(crop_type.lower(), []),
        "count": len(disease_database.get(crop_type.lower(), []))
    }

# Example 3: Resource with Multiple Parameters - Weather Data
@mcp.resource("weather://location/{latitude}/{longitude}/current")
async def get_weather_data(latitude: str, longitude: str):
    """
    Resource providing current weather data for a location
    URI: weather://location/40.7128/74.0060/current
    """
    # Simulated weather data - in real app, would fetch from API
    return {
        "location": {
            "latitude": float(latitude),
            "longitude": float(longitude)
        },
        "temperature": 22.5,
        "humidity": 65,
        "conditions": "partly_cloudy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Example 4: Resource - Farm Information
@mcp.resource("farm://profile/{farm_id}")
async def get_farm_profile(farm_id: str):
    """
    Resource providing farm profile information
    URI: farm://profile/FARM_001
    """
    farms = {
        "FARM_001": {
            "farm_name": "Green Valley Farms",
            "owner": "John Smith",
            "total_area": 500,
            "crops": ["wheat", "corn", "soybeans"],
            "established": "1985"
        },
        "FARM_002": {
            "farm_name": "Sunrise Agricultural Co.",
            "owner": "Maria Garcia",
            "total_area": 750,
            "crops": ["rice", "vegetables"],
            "established": "2005"
        }
    }
    return farms.get(farm_id, {"error": "Farm not found"})

# Example 5: Resource - Disease Statistics (Aggregated Read-Only Data)
@mcp.resource("statistics://diseases/summary")
async def get_disease_statistics():
    """
    Resource providing aggregated disease statistics
    Read-only summary data
    """
    return {
        "total_cases": 1247,
        "active_cases": 342,
        "resolved_cases": 905,
        "by_severity": {
            "critical": 45,
            "high": 123,
            "moderate": 174,
            "low": 905
        },
        "most_common_diseases": [
            {"name": "Late Blight", "cases": 234},
            {"name": "Powdery Mildew", "cases": 189},
            {"name": "Rust", "cases": 156}
        ],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@mcp.prompt()
def generate_search_prompt(disease: str, num_teatment: int = 5) -> str:
    """Generate a prompt for Claude to find and discuss academic papers on a specific disease."""
    return f"""Search for {num_teatment} academic papers about '{disease}' using the search_papers tool. 

        Follow these instructions:
        1. First, search for papers using search_papers(disease='{disease}', max_results={num_teatment})
        2. For each paper found, extract and organize the following information:
        - Paper title
        - Authors
        - Publication date
        - Brief summary of the key findings
        - Main contributions or innovations
        - Methodologies used
        - Relevance to the disease '{disease}'

        3. Provide a comprehensive summary that includes:
        - Overview of the current state of research in '{disease}'
        - Common themes and trends across the papers
        - Key research gaps or areas for future investigation
        - Most impactful or influential papers in this area

        4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.

        Please present both detailed information about each paper and a high-level synthesis of the research landscape in {disease}."""

# Example 1: Tool - Register New Disease Case
@mcp.tool()
async def register_disease_case(
    disease_name: str,
    farm_id: str,
    crop_type: str,
    severity: str,
    detected_by: str
) -> dict:
    """
    Tool to register a new crop disease case
    This performs an action - creates a new record in the database
    """
    # This has side effects - it modifies data
    disease_id = f"DISEASE_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Simulate database insertion
    new_case = {
        "disease_id": disease_id,
        "disease_name": disease_name,
        "farm_id": farm_id,
        "crop_type": crop_type,
        "severity": severity,
        "detected_by": detected_by,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # In real implementation, would save to database here
    # db.insert_disease(new_case)
    
    return {
        "success": True,
        "disease_id": disease_id,
        "message": f"Disease case {disease_id} registered successfully",
        "data": new_case
    }

# Example 2: Tool - Update Disease Status
@mcp.tool()
async def update_crop_disease_status(
    disease_id: str,
    new_status: str,
    updated_by: str,
    notes: str = None
) -> dict:
    """
    Tool to update the status of a disease case
    This modifies existing data
    """
    # This is an action that changes state
    valid_statuses = ["active", "monitoring", "controlled", "resolved", "chronic"]
    
    if new_status not in valid_statuses:
        return {
            "success": False,
            "error": f"Invalid status. Must be one of: {valid_statuses}"
        }
    
    # Simulate database update
    # db.update_disease_status(disease_id, new_status, updated_by)
    
    return {
        "success": True,
        "disease_id": disease_id,
        "previous_status": "active",  # Would fetch from DB
        "new_status": new_status,
        "updated_by": updated_by,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes
    }

# Example 3: Tool - Apply Treatment
@mcp.tool()
async def apply_crop_disease_treatment(
    disease_id: str,
    product_name: str,
    quantity: float,
    area_treated: float,
    applied_by: str
) -> dict:
    """
    Tool to record a treatment application
    This creates a new treatment record and may trigger notifications
    """
    application_id = f"APP_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # This action creates a record and might send notifications
    treatment_record = {
        "application_id": application_id,
        "disease_id": disease_id,
        "product_name": product_name,
        "quantity": quantity,
        "area_treated": area_treated,
        "applied_by": applied_by,
        "application_date": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    }
    
    # Would save to database and send notifications
    # db.insert_treatment(treatment_record)
    # notification_service.send_treatment_alert(disease_id)
    
    return {
        "success": True,
        "application_id": application_id,
        "message": f"Treatment application {application_id} recorded",
        "next_steps": "Monitor for effectiveness in 7-14 days",
        "data": treatment_record
    }

# Example 4: Tool - Calculate Disease Risk Score
@mcp.tool()
async def calculate_crop_disease_risk(
    crop_type: str,
    temperature: float,
    humidity: float,
    rainfall: float,
    season: str
) -> dict:
    """
    Tool to calculate disease risk score based on environmental factors
    This performs computation and returns actionable insights
    """
    # This is a computation tool
    base_risk = 0.0
    
    # Risk factors based on temperature
    if 20 <= temperature <= 30:
        base_risk += 30
    elif temperature > 30:
        base_risk += 15
    
    # Risk factors based on humidity
    if humidity > 80:
        base_risk += 40
    elif humidity > 60:
        base_risk += 20
    
    # Risk factors based on rainfall
    if rainfall > 10:
        base_risk += 30
    
    # Normalize to 0-100 scale
    risk_score = min(base_risk, 100)
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "high"
        recommendation = "Immediate preventive measures recommended"
    elif risk_score >= 40:
        risk_level = "moderate"
        recommendation = "Increase monitoring frequency"
    else:
        risk_level = "low"
        recommendation = "Continue normal monitoring"
    
    return {
        "crop_type": crop_type,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "contributing_factors": {
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall,
            "season": season
        },
        "recommendation": recommendation,
        "calculated_at": datetime.now(timezone.utc).isoformat()
    }


# Example 5: Tool - Send Alert Notification
@mcp.tool()
async def send_crop_disease_alert(
    disease_id: str,
    recipient_email: str,
    urgency: str,
    message: str
) -> dict:
    """
    Tool to send alert notifications about disease outbreaks
    This performs an external action (sending email)
    """
    # This has external side effects - sends an email
    alert_id = f"ALERT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Simulate sending email
    # email_service.send_alert(recipient_email, message)
    
    return {
        "success": True,
        "alert_id": alert_id,
        "disease_id": disease_id,
        "recipient": recipient_email,
        "urgency": urgency,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "message": "Alert notification sent successfully"
    }

# Example 6: Tool - Generate Report
@mcp.tool()
def generate_crop_disease_report(
    farm_id: str,
    start_date: str,
    end_date: str,
    report_format: str = "pdf"
) -> dict:
    """
    Tool to generate disease reports for a specific period
    This performs computation and file generation
    """
    report_id = f"REPORT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Simulate report generation
    # report_data = db.get_disease_data(farm_id, start_date, end_date)
    # report_file = report_generator.create(report_data, report_format)
    
    return {
        "success": True,
        "report_id": report_id,
        "farm_id": farm_id,
        "period": {
            "start": start_date,
            "end": end_date
        },
        "format": report_format,
        "file_url": f"https://reports.example.com/{report_id}.{report_format}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_cases": 15,
            "active_cases": 5,
            "treatments_applied": 12
        }
    }
    
if __name__ == "__main__":
    mcp.run(transport='stdio')