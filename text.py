import time
import folium
import streamlit as st
import random
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json
import  numpy as np
from streamlit_folium import folium_static
import pandas as pd

import asyncio
from folium.plugins import AntPath
from datetime import date
import plotly.io as pio


def load_aircraft_data(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return []

# Định nghĩa hàm để lấy tọa độ từ tên thành phố
# Define a function to get coordinates from a city name
def get_coordinates(city_name):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude
    else:
        return None

# Define the Aircraft class
class Aircraft:
    def __init__(self, id_Aircraft, initial_temperature=300, power=100, departure="", destination=""):
        self.id_Aircraft = id_Aircraft
        self.temperature = initial_temperature
        self.power = power
        self.departure = departure
        self.destination = destination

    def simulate_engine_operation(self):
        temperature_change = random.uniform(-10, 10)
        self.temperature += temperature_change

    def get_temperature(self):
        return self.temperature

# Define the AircraftManager class
class AircraftManager:
    def __init__(self):
        self.aircraft_list = []
        self.guest_list = []


    def update_from_json(self, filename):
        try:
            with open(filename, "r") as json_file:
                existing_data = json.load(json_file)
                for id_Aircraft, info in existing_data.items():
                    aircraft = Aircraft(id_Aircraft, **info)
                    self.add_aircraft(aircraft)
        except FileNotFoundError:
            print(f"File {filename} not found.")

    def create_aircraft(self):
        data = []
        location = ["Hue,VietNam", "HoChiMinh,VietNam", "HaNoi,VietNam", "DaNang,VietNam", "QuangNinh,VietNam",
                    "KienGiang,VietNam", "PhuQuoc,VietNam", "Vinh,VietNam", "CanTho,VietNam", "ConDao,VietNam"]

        for i in range(100):
            random_integer = random.randint(1, 10 )
            aircraft_id = f"Aircraft-{random_integer}"
            temperature = 100
            power = 100
            departure = random.choice(location)
            destination = random.choice(location)

            # Ensure departure and destination are different
            while departure == destination:
                destination = random.choice(location)

            aircraft = Aircraft(aircraft_id, temperature, power, departure, destination)
            data.append(aircraft.__dict__)

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(data)

        # Save the DataFrame to an Excel file
        data_chuyen_bay = "data_chuyen_bay.xlsx"
        df.to_excel(data_chuyen_bay, index=False)

        return data_chuyen_bay


    def add_aircraft(self, aircraft):
        self.aircraft_list.append(aircraft)

    def get_aircraft_by_id(self, aircraft_id):
        for aircraft in self.aircraft_list:
            if aircraft.id_Aircraft == aircraft_id:
                return aircraft
        return None

    def monitor_all_aircraft(self, num_iterations=5):
        for i in range(num_iterations):
            for aircraft in self.aircraft_list:
                aircraft.simulate_engine_operation()
                current_temp = aircraft.get_temperature()
                st.write(f"Temperature of Aircraft {aircraft.id_Aircraft}: {current_temp:.2f} °C")
                self.control_mechanism(aircraft)

    def control_mechanism(self, aircraft):
        safe_temperature_range = (100, 110)
        current_temp = aircraft.get_temperature()

        if current_temp < safe_temperature_range[0] or current_temp > safe_temperature_range[1]:
            #st.write(f"Temperature of Aircraft {aircraft.id_Aircraft} is outside the safe range.")
            new_power = 105 / aircraft.power
            #st.write(f"Adjusting power to: {new_power:.2f}")
            aircraft.power = new_power
            aircraft.temperature = 105
            #st.write(f"Due to overheating, Aircraft {aircraft.id_Aircraft} has reduced power and temperature is back to normal.")
        #else:
            #st.write(f"Temperature of Aircraft {aircraft.id_Aircraft} is within the safe range.")



class Guest:
    def __init__(self, hoten, tuoi, cccd, gioitinh, ngaysinh, diachi):
        self.hoten = hoten
        self.tuoi = self.validate_age(tuoi)  # Kiểm tra và gán tuổi
        self.cccd = self.validate_cccd(cccd)  # Kiểm tra và gán số CCCD
        self.gioitinh = self.validate_gender(gioitinh)  # Kiểm tra và gán giới tính
        self.ngaysinh = self.validate_birthdate(ngaysinh)  # Kiểm tra và gán ngày sinh
        self.diachi = diachi

    def validate_age(self, age):
        if 18 <= age <= 100:
            return age
        else:
            raise ValueError("Tuổi không hợp lệ. Vui lòng nhập tuổi từ 18 đến 100.")

    def validate_cccd(self, cccd):
        if len(cccd) == 9 and cccd.isdigit():
            return cccd
        else:
            raise ValueError("Số CCCD không hợp lệ. Vui lòng nhập 9 chữ số.")

    def validate_gender(self, gender):
        if gender.lower() in ["nam", "nữ"]:
            return gender
        else:
            raise ValueError("Giới tính không hợp lệ. Vui lòng nhập 'Nam' hoặc 'Nữ'.")

    def validate_birthdate(self, birthdate):
        try:
            ngay_sinh = date.fromisoformat(birthdate)
            if ngay_sinh <= date.today():
                return ngay_sinh
            else:
                raise ValueError("Ngày sinh không hợp lệ. Vui lòng không nhập ngày trong tương lai.")
        except ValueError:
            raise ValueError("Ngày sinh không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD.")

def calculate_mach(speed, altitude):
    sos = 665
    mach = speed / sos
    m = altitude * 0.00356
    temp_h = 58.9 - m
    p = altitude * 0.000523
    press = 14.694 - p
    return mach, temp_h, press

def calculate_pres_temp(mach,throttle,altitude):
    temp_start = [518, 518, 939, 2500, 339 , 339, 339, 339]
    press_start =[14.6,14.6,117.5,117.5,6.8,6.8,6.8,6.8]
    result_temp =[]
    result_press =[]

    for i in range(len(temp_start)):
        s = temp_start[i]*(1+0.2*mach**2) - ((altitude/1000)*3.6)
        result_temp.append(s)
    result_temp[3] = throttle * 25
    result_temp[4] = temp_start[4]*(1+0.2*mach**2) - ((altitude/1000)*3.6) + ((throttle-30)/10)*268
    result_temp[5] = temp_start[5]*(1+0.2*mach**2) - ((altitude/1000)*3.6) + ((throttle-30)/10)*268
    result_temp[6] = temp_start[6]*(1+0.2*mach**2) - ((altitude/1000)*3.6) + ((throttle-30)/10)*268
    result_temp[7] = temp_start[7]*(1+0.2*mach**2) - ((altitude/1000)*3.6) + ((throttle-30)/10)*268
    for i in range(len(temp_start)):
        s = press_start[i] * (1 + 0.2 * mach ** 2) ** (1.4 / (1.4 - 1))
        result_press.append(s)
    return result_press, result_temp
#-------------------------------------------------------------------------------------------------------------------------------------------------
# Create an AircraftManager object
aircraft_manager = AircraftManager()
# Create and add two Aircraft objects
# Display the Streamlit interface


st.sidebar.title("Danh sách chức năng")
#----------------------------------------------------------------------------------------------------------------------------------------------



#DANH SACH MAY BAY(FUNCTION)
st.title("Danh sách các máy bay")
list_aircraft = st.sidebar.button("Danh sách máy bay")
if list_aircraft:
    st.write("Danh sách máy bay:")
    aircraft_manager.update_from_json('aircraft_info.json')
    for aircraft in aircraft_manager.aircraft_list:
        st.write(f"- Máy bay {aircraft.id_Aircraft}: Khởi hành từ {aircraft.departure}, đến {aircraft.destination}")
#-------------------------------------------------------------------------------------------------------------------------------------------------





#NhietDo

move_aircraft = st.sidebar.button("Theo dõi nhiệt độ")
if move_aircraft:
    st.title("Theo dõi nhiệt độ")
    aircraft_manager.update_from_json('aircraft_info.json')
    temperature_data = {}

    # Simulate engine operation and collect temperature data for each aircraft
    for aircraft in aircraft_manager.aircraft_list:
        temperature_data[aircraft.id_Aircraft] = []

        # Simulate engine operation for 10 iterati.ons
        for _ in range(100):
            temperature_data[aircraft.id_Aircraft].append(aircraft.get_temperature())
            aircraft_manager.control_mechanism(aircraft)
            aircraft.simulate_engine_operation()



    # Create a time array (assuming each iteration represents 1 minute)
    time_array = np.arange(0, 100, 1)

    # Plot temperature data for each aircraft
    plt.figure(figsize=(10, 6))
    for aircraft_id, temp_values in temperature_data.items():
        plt.plot(time_array, temp_values, label=f"Aircraft {aircraft_id}")

    plt.xlabel("Time (minutes)")
    plt.ylabel("Temperature (°C)")
    plt.title("Temperature vs. Time for Each Aircraft")
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

    for aircraft in aircraft_manager.aircraft_list:
        temperature_data[aircraft.id_Aircraft] = []

        # Simulate engine operation for 10 iterati.ons
        for _ in range(100):
            temperature_data[aircraft.id_Aircraft].append(aircraft.get_temperature())

            aircraft_manager.control_mechanism(aircraft)
            aircraft.simulate_engine_operation()

    #lay du lieu
    df = pd.DataFrame(temperature_data)

    # Save the DataFrame to an Excel file
    output_filename = "temperature_data.xlsx"
    df.to_excel(output_filename, index=False)

    st.write(f"Temperature data saved to {output_filename}")
    count_per_aircraft = {}
    for aircraft, temps in temperature_data.items():
        count = 0
        for temp in temps:
            if 100 < temp < 110:
                count += 1
        st.write(f"Tổng số lần máy bay{aircraft} có nhiệt độ ngoài ngưỡng an toàn là: {count}")
        if count >= 50:
            st.write(f"Máy bay {aircraft} đã vượt số lần ngoài nhiệt độ an toàn cần bảo trì ngay!")



#-----------------------------------------------------------




#-------------------------------------------------------------------------------------------------------------------------




#BIEU DO (FUNCTION)
map_aircraft = st.sidebar.button("Biểu đồ tổng quan")
if map_aircraft:
    st.title("Biểu đồ tổng quan")
    aircraft_manager.update_from_json('aircraft_info.json')

    m = folium.Map(location=[16.463730, 107.594978], zoom_start=5.45)
    folium.Marker(location=[16.463730, 107.594978], popup="Hue").add_to(m)

    departure_coords = [(get_coordinates(aircraft.departure)) for aircraft in aircraft_manager.aircraft_list]
    destination_coords = [(get_coordinates(aircraft.destination)) for aircraft in aircraft_manager.aircraft_list]

    # Kiểm tra xem có tọa độ không
    for i in range(len(aircraft_manager.aircraft_list)):
        if departure_coords[i] and destination_coords[i]:
            folium.Marker(location=departure_coords[i], popup=aircraft_manager.aircraft_list[i].departure,icon=folium.Icon(color='blue')).add_to(m)
            folium.Marker(location=destination_coords[i], popup=aircraft_manager.aircraft_list[i].destination,icon=folium.Icon(color='red')).add_to(m)
            #folium.PolyLine([departure_coords[i], destination_coords[i]], color="blue").add_to(m)
            folium.PolyLine([departure_coords[i], destination_coords[i]], color="blue", dash_array="5, 5").add_to(m)
            #ant_path = AntPath(locations=departure_coords + destination_coords, color='blue', delay=1000)
            #ant_path.add_to(m)
        else:
            st.write("Không tìm thấy tọa độ cho điểm khởi hành hoặc điểm đến.")
            for aircraft in aircraft_manager.aircraft_list:
                st.write(f"VỊ TRÍ BẮT ĐẦU {aircraft.id_Aircraft} là : {aircraft.departure}")
                st.write(get_coordinates(aircraft.departure))
                st.write(f"VỊ TRÍ KẾT THÚC {aircraft.id_Aircraft} là : {aircraft.destination}")
                st.write(get_coordinates(aircraft.destination))
    folium_static(m)
    st.write("Danh sách máy bay hiện hoạt động:")
    for aircraft in aircraft_manager.aircraft_list:
        st.write(f"- Máy bay {aircraft.id_Aircraft}: Khởi hành từ {aircraft.departure}, đến {aircraft.destination}")
#----------------------------------------------------------------------------------
#PhanTichChuyenBay
travel_aircraft = st.sidebar.button("Phân tích thị trường")

if travel_aircraft:
    st.title("Phân tích thị trường")
    document = aircraft_manager.create_aircraft()
    excel_file = "data_chuyen_bay.xlsx"
    df = pd.read_excel(excel_file)

    # In ra màn hình
    st.write(df)
    iid_counts = df['id_Aircraft'].value_counts()

# Create a bar chart to visualize the data
    plt.figure(figsize=(8, 6))
    plt.bar(iid_counts.index, iid_counts.values, color='skyblue')
    plt.xlabel('id_Aircraft')
    plt.ylabel('Số lần xuất hiện')
    plt.title('Biểu đồ số lần xuất hiện của mỗi id_Aircraft')
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(plt)
    ###departure
    iid_countss = df['departure'].value_counts()

    # Create a bar chart to visualize the data
    plt.figure(figsize=(8, 6))
    plt.bar(iid_countss.index, iid_countss.values, color='skyblue')
    plt.xlabel('Địa điểm')
    plt.ylabel('Số lần xuất hiện')
    plt.title('Biểu đồ số lần xuất hiện của mỗi điểm bắt đầu')
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(plt)
    ###
    iid_countsss = df['destination'].value_counts()

    # Create a bar chart to visualize the data
    plt.figure(figsize=(8, 6))
    plt.bar(iid_countsss.index, iid_countsss.values, color='skyblue')
    plt.xlabel('Địa điểm')
    plt.ylabel('Số lần xuất hiện')
    plt.title('Biểu đồ số lần xuất hiện của mỗi điểm kết thúc')
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(plt)
#--------------------------------------------------------------------------------------------------------------------------------------------
#Du Bao Thoi Tiet






#----------------------------------------------------------------------------------------------------------------------------------------------
#
#----------------------------------------------------------------------------------------------------------------------------------------------
#TAO MAY BAy (FUNCTION)

add_aircraft = st.sidebar.title("Thêm Máy Bay")
id_Aircraft = st.sidebar.text_input("ID Máy Bay")
initial_temperature = st.sidebar.number_input("Nhiệt Độ Ban Đầu", value=100)
power = st.sidebar.number_input("Công Suất", value=100)
departure = st.sidebar.text_input("Điểm Khởi Hành")
destination = st.sidebar.text_input("Điểm Đến")
create_aircraft = st.sidebar.button("Tạo Máy Bay")

if create_aircraft:
    try:
        with open("aircraft_info.json", "r") as json_file:
            existing_data = json.load(json_file)
    except FileNotFoundError:
        existing_data = {}

    if not id_Aircraft or not departure or not destination:
        st.sidebar.error("Vui lòng nhập đủ thông tin cho máy bay!")
    elif any(aircraft.id_Aircraft == id_Aircraft for aircraft in aircraft_manager.aircraft_list):
        st.sidebar.error(f"ID {id_Aircraft} đã tồn tại. Vui lòng chọn ID khác.")
    else:
        aircraft = Aircraft(id_Aircraft, initial_temperature, power, departure, destination)
        aircraft_manager.add_aircraft(aircraft)
        st.sidebar.success(f"Máy bay {id_Aircraft} đã được tạo thành công!")

        # Cập nhật thông tin máy bay vào dữ liệu cũ
        existing_data[id_Aircraft] = {
            "initial_temperature": initial_temperature,
            "power": power,
            "departure": departure,
            "destination": destination
        }

        # Ghi dữ liệu mới vào tệp JSON
        with open("aircraft_info.json", "w") as json_file:
            json.dump(existing_data, json_file, indent=4)

        st.write(f"Thông tin máy bay đã được lưu vào aircraft_info.json.")

