import 'package:flutter/widgets.dart';

class Satir extends StatelessWidget {
  const Satir({super.key});

  @override
  Widget build(BuildContext context) {
    return const Row(children: [
      Expanded(
        child: Text('Uzun film adı'),
      ),
    ]);
  }
}
