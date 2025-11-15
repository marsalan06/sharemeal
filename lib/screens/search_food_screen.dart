import 'package:flutter/material.dart';

/// Lists available meals and lets requesters raise a booking request.
class SearchFoodScreen extends StatefulWidget {
  const SearchFoodScreen({super.key});

  @override
  State<SearchFoodScreen> createState() => _SearchFoodScreenState();
}

class _SearchFoodScreenState extends State<SearchFoodScreen> {
  final TextEditingController _searchController = TextEditingController();
  final List<Map<String, String>> _allFoods = const [
    {
      'title': 'Leftover Biryani',
      'location': 'PECHS Karachi',
      'quantity': '4 servings',
      'time': 'Pickup before 6 PM',
    },
    {
      'title': 'Chicken Rolls',
      'location': 'Gulshan',
      'quantity': '6 rolls',
      'time': 'Pickup before 5 PM',
    },
  ];

  List<Map<String, String>> get _filteredFoods {
    if (_searchController.text.isEmpty) {
      return _allFoods;
    }
    final query = _searchController.text.toLowerCase();
    return _allFoods.where((food) {
      return (food['title'] ?? '').toLowerCase().contains(query) ||
          (food['location'] ?? '').toLowerCase().contains(query);
    }).toList();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _requestFood(BuildContext context, Map<String, String> food) {
    // TODO: ApiService.requestFood should notify donor; no phone exposure yet.
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Request sent for ${food['title']}')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Discover Shared Meals'),
        actions: [
          IconButton(
            icon: const Icon(Icons.post_add_outlined),
            onPressed: () => Navigator.pushNamed(context, '/add-food'),
          ),
          IconButton(
            icon: const Icon(Icons.chat_bubble_outline),
            onPressed: () => Navigator.pushNamed(context, '/food-requests'),
          ),
        ],
        centerTitle: true,
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF4FDFB), Color(0xFFE1F6F4)],
            begin: Alignment.topRight,
            end: Alignment.bottomLeft,
          ),
        ),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
              child: TextField(
                controller: _searchController,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  hintText: 'Search meals or locations...',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            _searchController.clear();
                            setState(() {});
                          },
                        )
                      : null,
                ),
              ),
            ),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
                itemCount: _filteredFoods.length,
                itemBuilder: (ctx, i) {
                  final food = _filteredFoods[i];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Card(
                      clipBehavior: Clip.antiAlias,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  radius: 20,
                                  backgroundColor: theme.colorScheme.primary.withOpacity(0.12),
                                  child: Icon(
                                    Icons.restaurant_rounded,
                                    color: theme.colorScheme.primary,
                                    size: 20,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        food['title'] ?? '',
                                        style: theme.textTheme.titleMedium?.copyWith(
                                          fontWeight: FontWeight.w700,
                                          color: const Color(0xFF2B3A55),
                                        ),
                                        overflow: TextOverflow.ellipsis,
                                        maxLines: 1,
                                      ),
                                      const SizedBox(height: 4),
                                      Row(
                                        children: [
                                          const Icon(Icons.location_on_outlined, size: 16),
                                          const SizedBox(width: 4),
                                          Expanded(
                                            child: Text(
                                              food['location'] ?? '',
                                              style: theme.textTheme.bodySmall?.copyWith(
                                                color: const Color(0xFF6C7A92),
                                              ),
                                              overflow: TextOverflow.ellipsis,
                                              maxLines: 1,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                SingleChildScrollView(
                                  scrollDirection: Axis.horizontal,
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      _buildInfoChip(
                                        icon: Icons.people_alt_outlined,
                                        label: food['quantity'] ?? '',
                                      ),
                                      const SizedBox(width: 8),
                                      _buildInfoChip(
                                        icon: Icons.timer_outlined,
                                        label: food['time'] ?? '',
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(height: 8),
                                _buildInfoChip(
                                  icon: Icons.shield_moon_outlined,
                                  label: 'Verified host',
                                ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            Row(
                              children: [
                                Expanded(
                                  child: OutlinedButton(
                                    onPressed: () => _requestFood(ctx, food),
                                    style: OutlinedButton.styleFrom(
                                      padding: const EdgeInsets.symmetric(vertical: 12),
                                      side: BorderSide(
                                        color: theme.colorScheme.primary.withOpacity(0.4),
                                      ),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                    ),
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Icon(Icons.volunteer_activism_outlined,
                                            color: theme.colorScheme.primary, size: 18),
                                        const SizedBox(width: 6),
                                        Text(
                                          'Request Meal',
                                          style: TextStyle(
                                            color: theme.colorScheme.primary,
                                            fontSize: 13,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: ElevatedButton(
                                    onPressed: () => _requestFood(ctx, food),
                                    style: ElevatedButton.styleFrom(
                                      padding: const EdgeInsets.symmetric(vertical: 12),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                    ),
                                    child: const Text(
                                      'Instant Request',
                                      style: TextStyle(fontSize: 13),
                                    ),
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
          ],
        ),
      ),
    );
  }

  Widget _buildInfoChip({required IconData icon, required String label}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFFEFF6FF),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: const Color(0xFF1FA2FF)),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              color: Color(0xFF1B3B5A),
              fontWeight: FontWeight.w600,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

