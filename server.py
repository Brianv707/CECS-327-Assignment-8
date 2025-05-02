import socket
import sys
import psycopg2
from datetime import datetime
import pytz

# Database connection info
connectionLink ="postgresql://neondb_owner:npg_1A8ZEeGuFJya@ep-morning-lake-a6h7yydl-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require"

# Device configuration
devices ={
    'refrigerator_1': {
        'board_name': 'Fridge Board',
        'sensors': {
            'moisture': 'Moisture Meter - Moisture Sensor',
            'current': 'ACS712 - Ammeter Sensor'
        }
    },
    'refrigerator_2': {
        'board_name': 'board 1 6c8aabc5-3cfe-4996-a04b-24a1c336e495',
        'sensors': {
            'current': 'sensor 1 6c8aabc5-3cfe-4996-a04b-24a1c336e495',
            'moisture': 'sensor 2 6c8aabc5-3cfe-4996-a04b-24a1c336e495'
        }
    },
    'dishwasher': {
        'board_name': 'Dishwasher Board',
        'sensors': {
            'water': 'Water Consumption Sensor',
            'current': 'ACS712 - Ammeter Sensor Dishwasher'
        }
    }
}

def connectionToDB():
    try:
        return psycopg2.connect(connectionLink)
    except Exception:
        return None

def currentUnixTime():
    return int(datetime.now(pytz.utc).timestamp())              #current time to unix timestamp

def unixToPST(unix_timestamp):
    utc_time =datetime.utcfromtimestamp(int(unix_timestamp))       #unix to PST datetime
    pst =pytz.timezone("America/Los_Angeles")
    pst_time =utc_time.replace(tzinfo=pytz.utc).astimezone(pst)
    return pst_time.strftime("%Y-%m-%d %H:%M:%S %Z")

def fetchRecords(connection, query, params=None):
    try:
        cursor =connection.cursor()
        cursor.execute(query, params or ())
        records =[row[0] for row in cursor.fetchall()]
        cursor.close()
        return records
    except Exception as e:
        print(f"Error fetching records: {e}")
        return []

def calculateKWH(readings):
    if not readings:
        return 0
    reading_sum =sum(readings)
    count =len(readings)
    return ((reading_sum - (2.5 * count)) / 0.185) * 120 / 60 / 1000    #used ACS712, has a .185 sensitivity, multiply by 120 as US standard voltage is 120, divide by 60 to turn to hours, divide by 1000 to turn to kilowatts-hour

def query1(connection):         #kkitchen fridge average moisture past 3 hours
    try:
        now_unix =currentUnixTime()
        three_hours_ago_unix =now_unix - (3 * 60 * 60)     #gets time 3 hours before current time
        
        device =devices['refrigerator_1']                  #looking at device of fridge 1
        moisture_sensor =device['sensors']['moisture']     #moisture sensor is the data from the moisture sensor
        
        records =fetchRecords(
            connection,         #Sql query
            """
            SELECT payload
            FROM "Assignment 8_virtual"
            WHERE payload->>'board_name' =%s
            AND (payload->>'timestamp')::numeric >=%s
            AND (payload->>'timestamp')::numeric <=%s
            """,
            (device['board_name'], three_hours_ago_unix, now_unix)
        )
        
        if not records:
            return "No moisture data available for the kitchen fridge in the past three hours."
        
        moisture_readings =[]          #lists initialized for readings and time
        timestamps =[]
        
        for record in records:
            if moisture_sensor in record:
                try:
                    moisture_readings.append(float(record[moisture_sensor]))    #changes reading to float and adds it to readings
                except (ValueError, TypeError):
                    continue
                    
            if 'timestamp' in record:
                try:
                    timestamps.append(int(record['timestamp']))
                except (ValueError, TypeError):
                    continue
        
        if not moisture_readings:
            return "No moisture sensor readings found in the data."
        
        avg_moisture =sum(moisture_readings) / len(moisture_readings)
        min_time =unixToPST(min(timestamps)) if timestamps else "N/A"          #converts start and end time to PST
        max_time =unixToPST(max(timestamps)) if timestamps else "N/A"
        
        return (f"The average moisture inside your kitchen fridge in the past three hours is {avg_moisture:.2f}%.\n"
               f"Data period: {min_time} to {max_time}\n")
            
    except Exception as e:
        return f"Error querying fridge moisture: {str(e)}"

def query2(connection):             #gets the average amount of water consumption from dishwasher
    try:
        device =devices['dishwasher']                  #device dishwasher
        water_sensor =device['sensors']['water']       #for data in water sensor for dishwasher
        
        records =fetchRecords(         #sql query
            connection,
            """
            SELECT payload
            FROM "Assignment 8_virtual"
            WHERE payload->>'board_name' =%s
            """,
            (device['board_name'],)
        )
        
        water_readings =[]     #initialize lists
        timestamps =[]
        
        for record in records:
            if water_sensor in record:
                try:
                    water_readings.append(float(record[water_sensor]))      #adds data to readings list
                except (ValueError, TypeError):
                    continue
                    
            if 'timestamp' in record:
                try:
                    timestamps.append(int(record['timestamp']))
                except (ValueError, TypeError):
                    continue
        
        if not water_readings:
            return "No water consumption data available for the dishwasher."
        
        avg_water =sum(water_readings) / len(water_readings)               #calculates average water consumption 
        min_time =unixToPST(min(timestamps)) if timestamps else "N/A"      #converts time to PST
        max_time =unixToPST(max(timestamps)) if timestamps else "N/A"
        
        return (f"The average water consumption in your smart dishwasher is {avg_water:.2f} gallons.\n"
               f"Data period: {min_time} to {max_time}\n")
            
    except Exception as e:
        return f"Error querying dishwasher water consumption: {str(e)}"

def query3(connection):                 #gets which device used the most electricity out of the 3
    try:
        results ={}
        
        for device_key, device_config in devices.items():       #loops through all devices
            records =fetchRecords(     #sql query
                connection,
                """
                SELECT payload
                FROM "Assignment 8_virtual"
                WHERE payload->>'board_name' =%s
                """,
                (device_config['board_name'],)
            )
            
            readings =[]
            current_sensor =device_config['sensors'].get('current')
            
            if current_sensor:
                for record in records:
                    if current_sensor in record:
                        try:
                            readings.append(float(record[current_sensor]))      #adds data to readings list
                        except (ValueError, TypeError):
                            continue
            
            results[device_key] =calculateKWH(readings)
        
        highest =max(results.items(), key=lambda x: x[1])
        
        if highest[0] =='refrigerator_1':          #displays which device used the most kWh
            response =f"Refrigerator 1 consumed the most electricity with {results['refrigerator_1']:.2f} kWh. \n"
        elif highest[0] =='refrigerator_2':
            response =f"Refrigerator 2 consumed the most electricity with {results['refrigerator_2']:.2f} kWh. \n"
        else:
            response =f"Dishwasher consumed the most electricity with {results['dishwasher']:.2f} kWh. \n"
            
        response +=f"Refrigerator 1: {results['refrigerator_1']:.2f} kWh, \n"          #all device usage shown
        response +=f"Refrigerator 2: {results['refrigerator_2']:.2f} kWh, \n"
        response +=f"Dishwasher: {results['dishwasher']:.2f} kWh."
        
        return response
            
    except Exception as e:
        return f"Error comparing electricity consumption: {str(e)}"

def processQuery(query_number, connection):
    """Process the selected query"""
    queries ={
        "1": query1,
        "2": query2,
        "3": query3
    }
    
    return queries.get(query_number, lambda _: "Invalid query number. Please select 1-3.")(connection)

def server(host, port):
    """Start the socket server and handle client requests"""
    try:
        server_socket =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server listening on {host}:{port}...")
        
        connectionLink =connectionToDB()
        if not connectionLink:
            print("Failed to connect to database. Exiting.")
            return
        
        print("Successfully connected to database!")
        
        while True:
            client_socket, client_address =server_socket.accept()
            print(f"Connection established with {client_address}")
            
            try:
                while True:
                    data =client_socket.recv(1024)
                    if not data:
                        break
                    
                    query_number =data.decode('utf-8')
                    print(f"Received query number: {query_number}")
                    
                    response =processQuery(query_number, connectionLink)
                    client_socket.sendall(response.encode('utf-8'))
            
            except Exception as e:
                print(f"Error handling client request: {e}")
            finally:
                client_socket.close()
                print(f"Connection closed with {client_address}")
    
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        if 'connectionLink' in locals() and connectionLink:
            connectionLink.close()
        if 'server_socket' in locals():
            server_socket.close()

if __name__ =="__main__":
    host =input("Enter the server IP address: ")
    port =int(input("Enter the port number: (I used 12345) "))
    server(host, port)