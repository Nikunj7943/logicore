# Using the LogiCore Trip API from C# .NET

This guide shows you how to call the Trip API from a C# application, step by step.

---

## Prerequisites

- .NET 6 or later
- NuGet package: `Newtonsoft.Json` (or use built-in `System.Text.Json`)
- Your Frappe API Key and API Secret (see Step 1 below)
- Server URL: `http://logicore16.local` (replace with your actual server)

---

## Step 1 — Get Your API Key and Secret

1. Log in to the Frappe/ERPNext desk
2. Go to **Settings → Users**
3. Open the user account that will connect from C#
4. Scroll to **API Access** section
5. Click **Generate Keys**
6. Copy the **API Key** and **API Secret** — you will need both

> Store these in your app's configuration file (appsettings.json), never hardcode them in source code.

---

## Step 2 — Project Setup

### Install NuGet Package

```bash
dotnet add package Newtonsoft.Json
```

### appsettings.json

```json
{
  "TmsApi": {
    "BaseUrl": "http://logicore16.local",
    "ApiKey": "your_api_key_here",
    "ApiSecret": "your_api_secret_here"
  }
}
```

---

## Step 3 — Create the API Client Class

Create a file called `TmsApiClient.cs` in your project:

```csharp
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

public class TmsApiClient
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;

    public TmsApiClient(string baseUrl, string apiKey, string apiSecret)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _http = new HttpClient();

        // Set the Authorization header — Frappe uses "token key:secret" format
        _http.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("token", $"{apiKey}:{apiSecret}");

        _http.DefaultRequestHeaders.Accept.Add(
            new MediaTypeWithQualityHeaderValue("application/json"));
    }

    // Helper: extract the "message" field Frappe wraps all responses in
    private T ParseResponse<T>(string json)
    {
        var root = JObject.Parse(json);
        return root["message"].ToObject<T>();
    }
}
```

---

## Step 4 — Read Trips (List with Filters)

Add this method to `TmsApiClient`:

```csharp
public async Task<TripListResult> GetTripsAsync(
    string fromDate  = null,
    string toDate    = null,
    string customer  = null,
    string branch    = null,
    string tripStatus = null,
    int page         = 1,
    int pageSize     = 20)
{
    // Build the query string
    var query = new List<string>
    {
        $"page={page}",
        $"page_size={pageSize}"
    };

    if (!string.IsNullOrEmpty(fromDate))   query.Add($"from_date={fromDate}");
    if (!string.IsNullOrEmpty(toDate))     query.Add($"to_date={toDate}");
    if (!string.IsNullOrEmpty(customer))   query.Add($"customer={customer}");
    if (!string.IsNullOrEmpty(branch))     query.Add($"branch={branch}");
    if (!string.IsNullOrEmpty(tripStatus)) query.Add($"trip_status={tripStatus}");

    var url = $"{_baseUrl}/api/method/logicore.logicore.api.get_trips?{string.Join("&", query)}";

    var response = await _http.GetStringAsync(url);
    return ParseResponse<TripListResult>(response);
}
```

**Usage:**
```csharp
var result = await client.GetTripsAsync(
    fromDate: "2026-01-01",
    toDate:   "2026-03-31",
    page:     1,
    pageSize: 10
);

Console.WriteLine($"Total trips: {result.Total}");
foreach (var trip in result.Data)
{
    Console.WriteLine($"{trip.Name} | {trip.Customer} | {trip.TripStatus}");
}
```

---

## Step 5 — Read a Single Trip

```csharp
public async Task<Trip> GetTripAsync(string tripName)
{
    var url = $"{_baseUrl}/api/method/logicore.logicore.api.get_trip?trip_name={tripName}";

    var response = await _http.GetStringAsync(url);
    return ParseResponse<Trip>(response);
}
```

**Usage:**
```csharp
var trip = await client.GetTripAsync("032600001");
Console.WriteLine($"Customer: {trip.Customer}");
Console.WriteLine($"Origin: {trip.OriginCity} → {trip.DestinationCity1}");
Console.WriteLine($"Status: {trip.TripStatus}");
```

---

## Step 6 — Create a New Trip

```csharp
public async Task<CreateResult> CreateTripAsync(object tripData)
{
    var url = $"{_baseUrl}/api/method/logicore.logicore.api.create_trip";

    // Frappe whitelist methods accept form-encoded POST data
    var formData = new FormUrlEncodedContent(new[]
    {
        new KeyValuePair<string, string>("data", JsonConvert.SerializeObject(tripData))
    });

    var httpResponse = await _http.PostAsync(url, formData);
    httpResponse.EnsureSuccessStatusCode();

    var json = await httpResponse.Content.ReadAsStringAsync();
    return ParseResponse<CreateResult>(json);
}
```

**Usage:**
```csharp
var newTrip = new
{
    tcntrip_date      = "2026-03-30",
    trip_type         = "FTL",
    branch            = "Mumbai HQ",
    origin_city       = "Mumbai",
    destination_city_1 = "Delhi",
    customer          = "Reliance Industries"
};

var result = await client.CreateTripAsync(newTrip);
Console.WriteLine($"Created trip: {result.Name}");
```

---

## Step 7 — Update an Existing Trip

```csharp
public async Task<UpdateResult> UpdateTripAsync(string tripName, object fieldsToUpdate)
{
    var url = $"{_baseUrl}/api/method/logicore.logicore.api.update_trip";

    var formData = new FormUrlEncodedContent(new[]
    {
        new KeyValuePair<string, string>("trip_name", tripName),
        new KeyValuePair<string, string>("data", JsonConvert.SerializeObject(fieldsToUpdate))
    });

    var httpResponse = await _http.PostAsync(url, formData);
    httpResponse.EnsureSuccessStatusCode();

    var json = await httpResponse.Content.ReadAsStringAsync();
    return ParseResponse<UpdateResult>(json);
}
```

**Usage:**
```csharp
// Close a trip and record the arrival time
await client.UpdateTripAsync("032600001", new
{
    trip_status      = "Close",
    arrival_date_time = "2026-03-30 18:30:00",
    end_km           = 15200
});
```

---

## Step 8 — Delete a Trip

```csharp
public async Task<string> DeleteTripAsync(string tripName)
{
    var url = $"{_baseUrl}/api/method/logicore.logicore.api.delete_trip";

    var formData = new FormUrlEncodedContent(new[]
    {
        new KeyValuePair<string, string>("trip_name", tripName)
    });

    var httpResponse = await _http.PostAsync(url, formData);
    httpResponse.EnsureSuccessStatusCode();

    var json = await httpResponse.Content.ReadAsStringAsync();
    var root = JObject.Parse(json);
    return root["message"].ToString();
}
```

**Usage:**
```csharp
var msg = await client.DeleteTripAsync("032600001");
Console.WriteLine(msg); // "Trip 032600001 deleted successfully"
```

---

## Step 9 — Data Models (POCOs)

Add these classes to your project so the JSON deserializes cleanly:

```csharp
// Trip list response wrapper
public class TripListResult
{
    [JsonProperty("data")]      public List<Trip> Data { get; set; }
    [JsonProperty("total")]     public int Total       { get; set; }
    [JsonProperty("page")]      public int Page        { get; set; }
    [JsonProperty("page_size")] public int PageSize    { get; set; }
}

// Single Trip record
public class Trip
{
    [JsonProperty("name")]                   public string Name                  { get; set; }
    [JsonProperty("tcntrip_date")]           public string TcntripDate           { get; set; }
    [JsonProperty("tcntrip_no")]             public string TcntripNo             { get; set; }
    [JsonProperty("lr_no")]                  public string LrNo                  { get; set; }
    [JsonProperty("lr_date")]                public string LrDate                { get; set; }
    [JsonProperty("indent_no")]              public string IndentNo              { get; set; }
    [JsonProperty("indent_date")]            public string IndentDate            { get; set; }
    [JsonProperty("so")]                     public string So                    { get; set; }
    [JsonProperty("company")]                public string Company               { get; set; }
    [JsonProperty("branch")]                 public string Branch                { get; set; }
    [JsonProperty("customer")]               public string Customer              { get; set; }
    [JsonProperty("vendor")]                 public string Vendor                { get; set; }
    [JsonProperty("trip_type")]              public string TripType              { get; set; }
    [JsonProperty("business_format")]        public string BusinessFormat        { get; set; }
    [JsonProperty("origin_city")]            public string OriginCity            { get; set; }
    [JsonProperty("origin_city_2")]          public string OriginCity2           { get; set; }
    [JsonProperty("destination_city_1")]     public string DestinationCity1      { get; set; }
    [JsonProperty("destination_city_2")]     public string DestinationCity2      { get; set; }
    [JsonProperty("origin_state")]           public string OriginState           { get; set; }
    [JsonProperty("destination_state")]      public string DestinationState      { get; set; }
    [JsonProperty("vehicle_no")]             public string VehicleNo             { get; set; }
    [JsonProperty("driver")]                 public string Driver                { get; set; }
    [JsonProperty("driver_mobile")]          public string DriverMobile          { get; set; }
    [JsonProperty("types_of_good")]          public string TypesOfGood           { get; set; }
    [JsonProperty("packages")]               public int? Packages                { get; set; }
    [JsonProperty("eway_bill_no")]           public string EwayBillNo            { get; set; }
    [JsonProperty("customer_invoice_no")]    public string CustomerInvoiceNo     { get; set; }
    [JsonProperty("customer_freight")]       public decimal? CustomerFreight     { get; set; }
    [JsonProperty("vendor_freight")]         public decimal? VendorFreight       { get; set; }
    [JsonProperty("total_vendor_freight")]   public decimal? TotalVendorFreight  { get; set; }
    [JsonProperty("total_trip_amount")]      public decimal? TotalTripAmount     { get; set; }
    [JsonProperty("trip_total_amount_billed")] public decimal? TripTotalAmountBilled { get; set; }
    [JsonProperty("total_detention_amount")] public decimal? TotalDetentionAmount { get; set; }
    [JsonProperty("total_additional_charges")] public decimal? TotalAdditionalCharges { get; set; }
    [JsonProperty("trip_status")]            public string TripStatus            { get; set; }
    [JsonProperty("pod_status")]             public string PodStatus             { get; set; }
    [JsonProperty("date_pod_uploaded_on_erp")] public string DatePodUploadedOnErp { get; set; }
    [JsonProperty("start_km")]               public int? StartKm                 { get; set; }
    [JsonProperty("end_km")]                 public int? EndKm                   { get; set; }
    [JsonProperty("total_km")]               public int? TotalKm                 { get; set; }
    [JsonProperty("standard_km")]            public string StandardKm            { get; set; }
    [JsonProperty("journey_time")]           public string JourneyTime           { get; set; }
    [JsonProperty("journey_time_400_kmsday")] public string JourneyTime400KmsDay { get; set; }
    [JsonProperty("remarks")]                public string Remarks               { get; set; }
}

// Create/Update response wrappers
public class CreateResult
{
    [JsonProperty("name")]    public string Name    { get; set; }
    [JsonProperty("message")] public string Message { get; set; }
}

public class UpdateResult
{
    [JsonProperty("name")]    public string Name    { get; set; }
    [JsonProperty("message")] public string Message { get; set; }
}
```

---

## Step 10 — Putting It All Together (Program.cs)

```csharp
using Microsoft.Extensions.Configuration;

var config = new ConfigurationBuilder()
    .AddJsonFile("appsettings.json")
    .Build();

var baseUrl   = config["TmsApi:BaseUrl"];
var apiKey    = config["TmsApi:ApiKey"];
var apiSecret = config["TmsApi:ApiSecret"];

var client = new TmsApiClient(baseUrl, apiKey, apiSecret);

// --- List trips in a date range ---
var list = await client.GetTripsAsync(fromDate: "2026-01-01", toDate: "2026-03-31");
Console.WriteLine($"Found {list.Total} trips");

// --- Get one trip ---
if (list.Data.Count > 0)
{
    var tripName = list.Data[0].Name;
    var trip = await client.GetTripAsync(tripName);
    Console.WriteLine($"Trip: {trip.Name}, Customer: {trip.Customer}, Status: {trip.TripStatus}");
}

// --- Create a trip ---
var created = await client.CreateTripAsync(new
{
    tcntrip_date       = "2026-03-30",
    trip_type          = "FTL",
    branch             = "Mumbai HQ",
    origin_city        = "Mumbai",
    destination_city_1 = "Delhi",
    customer           = "Reliance Industries"
});
Console.WriteLine($"New trip created: {created.Name}");

// --- Update the trip ---
await client.UpdateTripAsync(created.Name, new { trip_status = "Close" });
Console.WriteLine("Trip closed.");

// --- Delete the trip ---
var msg = await client.DeleteTripAsync(created.Name);
Console.WriteLine(msg);
```

---

## Error Handling

Frappe returns HTTP error codes on failures. Wrap your calls in try/catch:

```csharp
try
{
    var trip = await client.GetTripAsync("INVALID-NAME");
}
catch (HttpRequestException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
{
    Console.WriteLine("Trip not found.");
}
catch (HttpRequestException ex) when (ex.StatusCode == System.Net.HttpStatusCode.Forbidden)
{
    Console.WriteLine("Access denied — check API key permissions.");
}
catch (HttpRequestException ex)
{
    Console.WriteLine($"API error: {ex.Message}");
}
```

---

## Quick Reference

| Action | Method | Endpoint |
|---|---|---|
| List trips | GET | `/api/method/logicore.logicore.api.get_trips` |
| Get one trip | GET | `/api/method/logicore.logicore.api.get_trip` |
| Create trip | POST | `/api/method/logicore.logicore.api.create_trip` |
| Update trip | POST | `/api/method/logicore.logicore.api.update_trip` |
| Delete trip | POST | `/api/method/logicore.logicore.api.delete_trip` |

**Date format:** `YYYY-MM-DD` (e.g. `2026-03-30`)

**Trip Status values:** `Open`, `Close`, `Cancel`

**POD Status values:** `POD Not Uploaded`, `Original POD Uploaded`, `Duplicate POD Uploaded`
