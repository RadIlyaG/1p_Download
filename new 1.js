
public class Main {
  
  
  public static int CalControlDigit(String barCode) {
    int temp = 0;
    for (int i = 0; i < barCode.length(); i++) {
        if ((i % 2) == 0)
            temp += Integer.parseInt(String.valueOf(barCode.charAt(i))) * 3;
        else
            temp += Integer.parseInt(String.valueOf(barCode.charAt(i)));
        System.out.println("temp: " + temp);
    }
    temp = 10 - (temp % 10);
    if (temp == 10)
        return 0;
    else
        return temp;
  }

  public static void main(String[] args) {
	// EA1004489579
    String barcode = "100448957";
    int controlDigit = CalControlDigit(barcode);
    System.out.println("Control Digit: " + controlDigit);
  }
}  
