import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:network_info_plus/network_info_plus.dart';
import 'dart:convert';

import 'data/base_url.dart';

class StartAttendancePage extends StatefulWidget {
  const StartAttendancePage({super.key});

  @override
  State<StartAttendancePage> createState() => _StartAttendancePageState();
}

class _StartAttendancePageState extends State<StartAttendancePage> {
  bool isLoading = false;

  final String macAddress = "AA:BB:CC:DD:EE:FF";
  final int sessionId = 1;

  Future<void> _checkIn() async {
    setState(() => isLoading = true);

    // Get real Wi-Fi IP
    final info = NetworkInfo();
    final deviceIp = await info.getWifiIP();

    try {
      final response = await http.post(
        Uri.parse("http://$baseURL/attendance/check_in"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "mac": macAddress,
          "session_id": sessionId,
          "device_ip": deviceIp, // CRITICAL
        }),
      );

      setState(() => isLoading = false);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Check-in recorded for ${data['student']}"),
            backgroundColor: Colors.green,
          ),
        );
        return;
      }

      if (response.statusCode == 403) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("You must be on classroom Wi-Fi"),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }

      final data = jsonDecode(response.body);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(data['error']), backgroundColor: Colors.red),
      );
    } catch (e) {
      setState(() => isLoading = false);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Network error: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Check-In", style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Center(
        child: ElevatedButton(
          onPressed: isLoading ? null : _checkIn,
          child: isLoading
              ? const CircularProgressIndicator(color: Colors.white)
              : const Text("Check In"),
        ),
      ),
    );
  }
}
