import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key});

  Future<void> _clearHistory(BuildContext context) async {
    try {
      final currentUser = FirebaseAuth.instance.currentUser;
      final studentId = currentUser?.email?.split('@').first;

      final snapshot = await FirebaseFirestore.instance
          .collection('attendance')
          .where('id', isEqualTo: studentId)
          .get();

      for (var doc in snapshot.docs) {
        await doc.reference.delete();
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Attendance history cleared!")),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error clearing history: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentUser = FirebaseAuth.instance.currentUser;

    // Get the student's ID from their email (like u22100848)
    final studentId = currentUser?.email?.split('@').first;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Attendance History", style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: Column(
        children: [
          Expanded(
            child: StreamBuilder<QuerySnapshot>(
              stream: FirebaseFirestore.instance
                  .collection('attendance')
                  .where('id', isEqualTo: studentId)
                  .snapshots(),
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
                  return const Center(child: Text("No attendance records found."));
                }

                final records = snapshot.data!.docs;

                return ListView.builder(
                  itemCount: records.length,
                  itemBuilder: (context, index) {
                    final data = records[index].data() as Map<String, dynamic>;

                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                      color: Colors.teal[50],
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: ListTile(
                        title: Text(
                          data['course_name'] ?? 'Unknown Course',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          "Date: ${data['date']}\n"
                          "Check-in: ${data['check_in']}\n"
                          "Status: ${data['status']}",
                        ),
                        trailing: Icon(
                          data['status'] == 'present'
                              ? Icons.check_circle
                              : Icons.cancel,
                          color: data['status'] == 'present'
                              ? Colors.green
                              : Colors.red,
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
          TextButton(
            onPressed: () => _clearHistory(context),
            style: TextButton.styleFrom(
              foregroundColor: Colors.red,
              textStyle: const TextStyle(fontSize: 14),
            ),
            child: const Text("Clear History"),
          ),
          const SizedBox(height: 10),
        ],
      ),
    );
  }
}
