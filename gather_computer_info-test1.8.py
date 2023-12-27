import json
import pymssql
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ���ݿ��������ã���������SQL Server���ý��е���
DB_CONFIG = {
    "server": "db5.lead.cn",
    "user": "opsdb",
    "password": "opsdb1QAZ",
    "database": "OPSDB"
}


def query_employee_by_job_no(job_no):
    # ����API�ӿ�URL
    url = 'https://it.leadchina.cn/proxy/api/ehr/query_employee_by_job_no'
    # ʹ��form-data��ʽ�ύ'job_no'����
    headers = {}
    files = []
    data = {
        'job_no': job_no,
        # 'domain': 'leadchina.cn'
    }

    try:
        # ʹ��POST��ʽ����API�ӿ�
        response = requests.request("POST", url, headers=headers, data=data, files=files)

        # �������ص�JSON����
        result = response.json()

        # ���'errcode'�ֶ��Ƿ�Ϊ'0'����������Ӧ��ֵ
        if result.get('errcode') == '0':
            return True, result.get('data').get('accounts')[0]
        else:
            print(result)
            return False, None

    # ����API���ù����е��쳣
    except requests.RequestException as e:
        print(f"API call error: {e}")
        return False, None

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return False, None


@app.route('/gather_computer_info', methods=['POST'])
def gather_computer_info():
    data = request.json

    # ����У��  // employee_id login_username
    required_fields = ["employee_id", "computer_name", "bios_sn", "login_username"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"message": u"ʹ���˹����ֶ��Ǳ����ֶΣ�����Ϊ��!"}), 400
    try:
        # ʹ�ù��Ų�ѯ�������ţ�ͬʱУ�鹤���Ƿ�Ϸ�
        employee_id = data.get('employee_id')
        login_username = data.get('login_username')
        # # ������Windowsϵͳ��¼��һ��
        # if employee_id == login_username:
        #     pass
        # else:
        #     # �����˺ŵ�¼��ʹ������������Ա����
        #     pass
        is_success, employee_info = query_employee_by_job_no(job_no=data.get('employee_id'))
        level2_deptName = employee_info.get('level2_deptName', '') if is_success else ''
        if not is_success:
            return jsonify({"message": u"�����ʹ���˹��Ų����ڣ�������������ְԱ������!"}), 400

        # ���ӵ�SQL Server���ݿ�
        with pymssql.connect(**DB_CONFIG) as conn:
            cursor = conn.cursor()
            # �������ݱ���������ڣ�
            cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ComputerInfo' AND xtype='U')
            CREATE TABLE ComputerInfo (
                ID INT PRIMARY KEY IDENTITY(1,1),
                EmployeeId  NVARCHAR(255),
                LoginUsername NVARCHAR(255),
                ComputerName NVARCHAR(255),
                Brand NVARCHAR(255),
                Model NVARCHAR(255),
                BIOS_SN NVARCHAR(255),
                Motherboard_SN NVARCHAR(255),
                CPU_Cores INT,
                CPU_Model NVARCHAR(255),
                CPU_Frequency FLOAT,
                Memory_GB FLOAT,
                Wired_MAC NVARCHAR(255),
                Wireless_MAC NVARCHAR(255),
                level2_deptName NVARCHAR(255),
                GraphicsCards NVARCHAR(1000),  -- �������ڴ洢�Կ���Ϣ���ֶ�
                Os_Name NVARCHAR(1000),  -- ��������ϵͳ���Ƶ��ֶ�
                CreateTime DATETIME DEFAULT GETDATE(),
                UpdateTime DATETIME
            )
            ''')
            # ���Ψһ��Լ��
            cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='UQ_ComputerInfo' AND object_id = OBJECT_ID('ComputerInfo'))
            ALTER TABLE ComputerInfo
            ADD CONSTRAINT UQ_ComputerInfo UNIQUE (ComputerName, BIOS_SN)
            ''')

            # ����Ƿ����ƥ��ļ�¼
            cursor.execute("SELECT COUNT(*) FROM ComputerInfo WHERE ComputerName=%s AND BIOS_SN=%s",
                           (data['computer_name'], data['bios_sn']))
            count = cursor.fetchone()[0]

            if count:
                # ���¼�¼
                cursor.execute('''
                UPDATE ComputerInfo
                SET EmployeeId=%s, LoginUsername=%s, Brand=%s, Model=%s, Motherboard_SN=%s, CPU_Cores=%s, CPU_Model=%s,
                CPU_Frequency=%s, Memory_GB=%s, Wired_MAC=%s, Wireless_MAC=%s, level2_deptName=%s, GraphicsCards=%s, Os_Name=%s, UpdateTime=GETDATE()
                WHERE ComputerName=%s AND BIOS_SN=%s
                ''', (data.get('employee_id'), data['login_username'], data.get('brand', None), data.get('model', None),
                      data.get('motherboard_sn', None), data.get('cpu_cores', None), data.get('cpu_model', None),
                      data.get('cpu_frequency', None), data.get('memory_gb', None), data.get('wired_mac', None),
                      data.get('wireless_mac', None), level2_deptName, data.get('graphics_cards', None), data.get('os_name', None), data['computer_name'], data['bios_sn']))
            else:
                # �����¼�¼
                cursor.execute('''
                INSERT INTO ComputerInfo (EmployeeId, LoginUsername, ComputerName, Brand, Model, BIOS_SN, Motherboard_SN
                , CPU_Cores, CPU_Model, CPU_Frequency, Memory_GB, Wired_MAC, Wireless_MAC, level2_deptName, GraphicsCards, Os_Name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (data.get('employee_id'), data['login_username'], data['computer_name'], data.get('brand', None),
                      data.get('model', None),
                      data['bios_sn'], data.get('motherboard_sn', None), data.get('cpu_cores', None),
                      data.get('cpu_model', None), data.get('cpu_frequency', None), data.get('memory_gb', None),
                      data.get('wired_mac', None), data.get('wireless_mac', None), level2_deptName, data.get('graphics_cards', None), data.get('os_name', None)))

            conn.commit()

        return jsonify({"message": "Data stored successfully!"}), 200

    except pymssql.DatabaseError as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/sap_install_status', methods=['POST'])
def sap_install_status():
    data = request.json
    try:
        # ����У��
        required_fields = ["Timestamp", "ComputerName", "Status"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"message": u"��������!"}), 400

        with pymssql.connect(**DB_CONFIG) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO SapInstallStatus (Timestamp, ComputerName, Status, ErrorMessage)
                VALUES (%s, %s, %s, %s)
                ''', (data['Timestamp'], data['ComputerName'], data['Status'], data.get('ErrorMessage', '')))
            conn.commit()

        return jsonify({"message": "Data stored successfully!"}), 200

    except pymssql.DatabaseError as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"message": str(e)}), 500

def init_db():
    with pymssql.connect(**DB_CONFIG) as conn:
        cursor = conn.cursor()

        # �������ݱ���������ڣ�
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SapInstallStatus' AND xtype='U')
        CREATE TABLE SapInstallStatus (
            ID INT PRIMARY KEY IDENTITY(1,1),
            Timestamp DATETIME DEFAULT GETDATE(),
            ComputerName NVARCHAR(255),
            Status NVARCHAR(32),
            ErrorMessage NVARCHAR(4000),
        )
        ''')
        conn.commit()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', debug=True)            