import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:geocoding/geocoding.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:intl/intl.dart';

/// Hosts the flow for donors to post available meals + pickup coordinates.
class AddFoodScreen extends StatefulWidget {
  const AddFoodScreen({super.key});

  @override
  State<AddFoodScreen> createState() => _AddFoodScreenState();
}

class _AddFoodScreenState extends State<AddFoodScreen> {
  final _addressSearchCtrl = TextEditingController();
  final _titleCtrl = TextEditingController();
  final _locationCtrl = TextEditingController();
  final _quantityCtrl = TextEditingController();
  final _timeCtrl = TextEditingController();
  final _itemsCtrl = TextEditingController();
  GoogleMapController? _mapController;
  LatLng? _selectedLatLng;
  bool _isSearching = false;
  DateTime? _availableUntil;
  final List<String> _foodItems = [];
  final List<String> _unitOptions = ['servings', 'kg'];
  String _selectedUnit = 'servings';
  String _quantityValue = '';

  void _onMapTap(LatLng position) {
    setState(() {
      _selectedLatLng = position;
      _locationCtrl.text =
          '${position.latitude.toStringAsFixed(6)}, ${position.longitude.toStringAsFixed(6)}';
    });
  }

  Future<void> _searchAddress() async {
    final query = _addressSearchCtrl.text.trim();
    if (query.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter an address to search')),
      );
      return;
    }

    setState(() => _isSearching = true);
    try {
      final results = await locationFromAddress(query);
      if (results.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No results found for that address')),
        );
        return;
      }
      final location = results.first;
      final target = LatLng(location.latitude, location.longitude);
      setState(() {
        _selectedLatLng = target;
        _locationCtrl.text =
            '${target.latitude.toStringAsFixed(6)}, ${target.longitude.toStringAsFixed(6)}';
      });
      await _mapController?.animateCamera(
        CameraUpdate.newLatLngZoom(target, 14),
      );
    } catch (error) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Address lookup failed: $error')),
      );
    } finally {
      if (!mounted) return;
      setState(() => _isSearching = false);
    }
  }

  void _submitFood() {
    if (_selectedLatLng == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please pick a location on the map')),
      );
      return;
    }
    if (_quantityValue.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select servings or weight available')),
      );
      return;
    }
    if (_availableUntil == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select availability date & time')),
      );
      return;
    }
    if (_foodItems.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Add at least one food item')),
      );
      return;
    }

    // TODO: Call ApiService.postFood and handle success/error responses.
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Food availability posted')),
    );

    _titleCtrl.clear();
    _addressSearchCtrl.clear();
    _locationCtrl.clear();
    _quantityCtrl.clear();
    _timeCtrl.clear();
    _itemsCtrl.clear();
    setState(() {
      _selectedLatLng = null;
      _availableUntil = null;
      _quantityValue = '';
      _selectedUnit = 'servings';
      _foodItems.clear();
    });
  }

  Future<void> _pickQuantity() async {
    final numberController = TextEditingController(text: _quantityValue);
    String unitSelection = _selectedUnit;
    String? errorText;
    final result = await showModalBottomSheet<Map<String, String>>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return SafeArea(
              child: SingleChildScrollView(
                child: Padding(
                  padding: EdgeInsets.only(
                    left: 20,
                    right: 20,
                    top: 16,
                    bottom: 16 + MediaQuery.of(ctx).viewInsets.bottom,
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Specify total food availability',
                        style: Theme.of(ctx).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: numberController,
                        keyboardType:
                            const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(
                          labelText: 'Quantity',
                          hintText: 'e.g., 12',
                          errorText: errorText,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 10,
                        children: _unitOptions
                            .map(
                              (unit) => ChoiceChip(
                                label: Text(unit),
                                selected: unitSelection == unit,
                                onSelected: (_) {
                                  setSheetState(() {
                                    unitSelection = unit;
                                  });
                                },
                              ),
                            )
                            .toList(),
                      ),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () {
                            final text = numberController.text.trim();
                            final value = double.tryParse(text);
                            if (value == null || value <= 0) {
                              setSheetState(
                                () => errorText =
                                    'Enter a valid quantity greater than zero',
                              );
                              return;
                            }
                            Navigator.pop(ctx, {'value': text, 'unit': unitSelection});
                          },
                          child: const Text('Confirm'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );

    // Delay disposal until after widget is removed safely
    WidgetsBinding.instance.addPostFrameCallback((_) {
      numberController.dispose();
    });

    if (result != null) {
      final value = result['value']!;
      final unit = result['unit']!;
      if (!mounted) return;
      setState(() {
        _quantityValue = value;
        _selectedUnit = unit;
        _quantityCtrl.text = '$value $unit';
      });
    }
  }

  Future<void> _pickAvailability() async {
    final now = DateTime.now();
    final selectedDate = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: now,
      lastDate: now.add(const Duration(days: 90)),
    );
    if (selectedDate == null) return;

    final selectedTime = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(now.add(const Duration(hours: 1))),
    );

    if (selectedTime == null) return;

    final combined = DateTime(
      selectedDate.year,
      selectedDate.month,
      selectedDate.day,
      selectedTime.hour,
      selectedTime.minute,
    );

    final formatted = DateFormat('EEE, dd MMM • hh:mm a').format(combined);
    if (!mounted) return;
    setState(() {
      _availableUntil = combined;
      _timeCtrl.text = formatted;
    });
  }

  void _addFoodItem() {
    final item = _itemsCtrl.text.trim();
    if (item.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a food item before adding')),
      );
      return;
    }
    if (!mounted) return;
    setState(() {
      _foodItems.add(item);
    });
    _itemsCtrl.clear();
  }

  void _removeFoodItem(String item) {
    if (!mounted) return;
    setState(() {
      _foodItems.remove(item);
    });
  }

  @override
  void dispose() {
    _addressSearchCtrl.dispose();
    _titleCtrl.dispose();
    _locationCtrl.dispose();
    _quantityCtrl.dispose();
    _timeCtrl.dispose();
    _itemsCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add Food Availability'),
        centerTitle: true,
      ),
      resizeToAvoidBottomInset: true,
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFFDFBFB), Color(0xFFE2D1C3)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: IntrinsicHeight(
                    child: Padding(
                      padding: EdgeInsets.fromLTRB(
                        20,
                        24,
                        20,
                        24 + bottomInset,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'Share what you have cooked and let others join the meal.',
                            style: theme.textTheme.bodyLarge?.copyWith(
                              color: const Color(0xFF4B4B4B),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Expanded(
                            child: Card(
                              margin: const EdgeInsets.only(top: 18),
                              child: Padding(
                                padding: const EdgeInsets.all(20),
                                child: SingleChildScrollView(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.stretch,
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      TextField(
                                        controller: _titleCtrl,
                                        decoration: const InputDecoration(
                                          labelText: 'Event / Title',
                                          hintText: 'Community Iftar at PECHS',
                                        ),
                                      ),
                                      const SizedBox(height: 18),
                                      TextField(
                                        controller: _addressSearchCtrl,
                                        textInputAction: TextInputAction.search,
                                        onSubmitted: (_) => _searchAddress(),
                                        decoration: InputDecoration(
                                          labelText: 'Search Address',
                                          hintText: 'e.g., Teen Talwar, Karachi',
                                          prefixIcon: const Icon(Icons.search),
                                          suffixIcon: Padding(
                                            padding: const EdgeInsets.only(right: 8),
                                            child: _isSearching
                                                ? const SizedBox(
                                                    width: 24,
                                                    height: 24,
                                                    child: CircularProgressIndicator(
                                                      strokeWidth: 2,
                                                    ),
                                                  )
                                                : IconButton(
                                                    icon: const Icon(Icons.arrow_forward),
                                                    onPressed: _searchAddress,
                                                  ),
                                          ),
                                        ),
                                      ),
                                      const SizedBox(height: 18),
                                      Text(
                                        'Pickup Location',
                                        style: theme.textTheme.titleMedium?.copyWith(
                                          color: theme.colorScheme.primary,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      const SizedBox(height: 12),
                                      ClipRRect(
                                        borderRadius: BorderRadius.circular(18),
                                        child: SizedBox(
                                          height: 220,
                                          child: GoogleMap(
                                            initialCameraPosition: const CameraPosition(
                                              target: LatLng(24.8607, 67.0011),
                                              zoom: 12,
                                            ),
                                            onMapCreated: (controller) =>
                                                _mapController = controller,
                                            onTap: _onMapTap,
                                            markers: {
                                              if (_selectedLatLng != null)
                                                Marker(
                                                  markerId: const MarkerId('pickup'),
                                                  position: _selectedLatLng!,
                                                ),
                                            },
                                            gestureRecognizers: {
                                              Factory<OneSequenceGestureRecognizer>(
                                                () => EagerGestureRecognizer(),
                                              ),
                                            },
                                            myLocationButtonEnabled: false,
                                            zoomControlsEnabled: false,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(height: 12),
                                      TextField(
                                        controller: _locationCtrl,
                                        readOnly: true,
                                        decoration: const InputDecoration(
                                          labelText: 'Selected Coordinates',
                                          hintText: 'Tap on the map to fill automatically',
                                          prefixIcon: Icon(Icons.location_on_outlined),
                                        ),
                                      ),
                                      const SizedBox(height: 18),
                                      TextField(
                                        controller: _quantityCtrl,
                                        readOnly: true,
                                        decoration: const InputDecoration(
                                          labelText: 'Quantity or Weight',
                                          hintText: 'Tap to choose servings / weight',
                                          prefixIcon: Icon(Icons.scale_outlined),
                                        ),
                                        onTap: _pickQuantity,
                                      ),
                                      const SizedBox(height: 16),
                                      TextField(
                                        controller: _timeCtrl,
                                        readOnly: true,
                                        decoration: const InputDecoration(
                                          labelText: 'Available Until',
                                          hintText: 'Tap to select date & time',
                                          prefixIcon: Icon(Icons.calendar_month_outlined),
                                        ),
                                        onTap: _pickAvailability,
                                      ),
                                      const SizedBox(height: 18),
                                      TextField(
                                        controller: _itemsCtrl,
                                        decoration: InputDecoration(
                                          labelText: 'Add Food Item',
                                          hintText: 'e.g., Chicken Biryani tray',
                                          prefixIcon:
                                              const Icon(Icons.restaurant_menu_outlined),
                                          suffixIcon: IconButton(
                                            icon: const Icon(Icons.add_circle_outline),
                                            onPressed: _addFoodItem,
                                          ),
                                        ),
                                        onSubmitted: (_) => _addFoodItem(),
                                      ),
                                      if (_foodItems.isNotEmpty) ...[
                                        const SizedBox(height: 12),
                                        Wrap(
                                          spacing: 8,
                                          runSpacing: 8,
                                          children: _foodItems
                                              .map(
                                                (item) => Chip(
                                                  label: Text(item),
                                                  deleteIcon: const Icon(Icons.close),
                                                  onDeleted: () => _removeFoodItem(item),
                                                ),
                                              )
                                              .toList(),
                                        ),
                                      ],
                                      const SizedBox(height: 24),
                                      ElevatedButton.icon(
                                        onPressed: _submitFood,
                                        icon: const Icon(Icons.cloud_upload_outlined),
                                        label: const Text('Post Availability'),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

