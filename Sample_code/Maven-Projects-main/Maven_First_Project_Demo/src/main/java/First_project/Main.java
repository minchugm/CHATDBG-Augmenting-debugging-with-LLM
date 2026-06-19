package First_project;
import java.nio.file.*;
import java.io.*;
public class Main {
    public static void main(String[] args) {
        String p = System.getenv("AI_DEBUG_INPUT_FILE");
        if (p != null && !p.isEmpty()) {
            try {
                byte[] b = Files.readAllBytes(Paths.get(p));
                int n = Math.min(b.length, 64);
                System.out.println("bytes=" + b.length);
                System.out.println(new String(b, 0, n));
                return;
            } catch (Exception e) {
                System.out.println("input-error=" + e.getMessage());
            }
        }
        democlass d = new democlass();
        System.out.println(d.demo());
    }
}
