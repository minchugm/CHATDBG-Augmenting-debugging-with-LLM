public class Main {
    public static void main(String[] args) {
        // Demonstrate the Greeter class
        Greeter g = new Greeter();
        System.out.println(g.greet("ChatDBG+"));

        System.out.println("\n--- Demonstrating other project components ---");

        // Call the main method from HelloWorld
        System.out.println("Output from HelloWorld.java:");       
        HelloWorld.main(args);

        // Call the main method from com.example.App
        System.out.println("\nOutput from com.example.App.java:");
        com.example.App.main(args);
    }
}