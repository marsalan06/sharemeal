import 'package:flutter/material.dart';

/// Shows incoming/outgoing requests so donors can accept, reject, or re-open.
class FoodRequestsScreen extends StatelessWidget {
  const FoodRequestsScreen({super.key});

  final List<Map<String, String>> requests = const [
    {'food': 'Leftover Biryani', 'from': 'Ali', 'contact': '03xx-xxxxxxx'},
    {'food': 'Chicken Rolls', 'from': 'Sara', 'contact': '03xx-xxxxxxx'},
  ];

  void _acceptRequest(BuildContext context, Map<String, String> request) {
    // TODO: API should respond with contact number for accepted bookings.
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Accepted. Share contact: ${request['contact']}')),
    );
  }

  void _rejectRequest(BuildContext context, Map<String, String> request) {
    // TODO: Collect optional rejection reason and publish to backend.
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Request rejected for ${request['food']}')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Food Requests'),
        centerTitle: true,
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFFDFCFB), Color(0xFFE2EBF0)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: ListView.builder(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
          itemCount: requests.length,
          itemBuilder: (ctx, i) {
            final request = requests[i];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          CircleAvatar(
                            radius: 24,
                            backgroundColor: theme.colorScheme.primary.withOpacity(0.1),
                            child: Icon(Icons.person_outline,
                                color: theme.colorScheme.primary),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        request['from'] ?? 'Requestor',
                                        style: theme.textTheme.titleMedium?.copyWith(
                                          fontWeight: FontWeight.w700,
                                          color: const Color(0xFF2B3A55),
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                        maxLines: 1,
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFFDCF3F5),
                                        borderRadius: BorderRadius.circular(16),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: const [
                                          Icon(Icons.schedule_outlined, size: 14, color: Color(0xFF1FA2FF)),
                                          SizedBox(width: 4),
                                          Text(
                                            'Pending',
                                            style: TextStyle(
                                              color: Color(0xFF1FA2FF),
                                              fontWeight: FontWeight.w600,
                                              fontSize: 11,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  request['food'] ?? '',
                                  style: theme.textTheme.bodyMedium?.copyWith(
                                    color: const Color(0xFF6C7A92),
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                  maxLines: 2,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF5F7FB),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.phone_in_talk_outlined, color: Color(0xFF4E5D78), size: 18),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                'Contact reveals only after you accept the request.',
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: const Color(0xFF4E5D78),
                                  fontWeight: FontWeight.w600,
                                ),
                                overflow: TextOverflow.ellipsis,
                                maxLines: 2,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          TextButton.icon(
                            onPressed: () => _rejectRequest(ctx, request),
                            icon: const Icon(Icons.close_rounded, size: 18),
                            label: const Text('Reject'),
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                            ),
                          ),
                          const Spacer(),
                          ElevatedButton.icon(
                            onPressed: () => _acceptRequest(ctx, request),
                            icon: const Icon(Icons.check_circle_outline),
                            label: const Text('Accept & Share'),
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

