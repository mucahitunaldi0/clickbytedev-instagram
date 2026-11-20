import 'package:flutter/widgets.dart';

Widget liste(List<String> urunler) {
  return ListView.builder(
    itemCount: urunler.length,
    itemBuilder: (context, i) {
      return Text(urunler[i]);
    },
  );
}
