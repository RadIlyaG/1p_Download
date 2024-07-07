unit General;

interface

uses
  SysUtils, Classes, DB, Ora, MemDS, DBAccess, Dialogs,
  IdTCPClient, IdBaseComponent, IdComponent, IdTCPConnection, IdHTTP, XSuperJSON, XSuperObject;



type
  TStringArray = array of string;
  TdmGeneral = class(TDataModule)
    OraSession1: TOraSession;
    sp001_MAC_ADDRES_ALLOC: TOraStoredProc;
    qry001_GetCurrMAC_Address: TOraQuery;
    qry001_GetCurrMAC_AddressMAC_ADDRESS: TStringField;
    qry002_GetIdNumberData: TOraQuery;
    qry002_GetIdNumberDataID: TFloatField;
    SaveDialog1: TSaveDialog;
    IdHTTP1: TIdHTTP;
    IdTCPClient1: TIdTCPClient;
  private
    { Private declarations }
    Success : Integer;


    procedure InsertValuesToVar(var FirstParam : String ; var SecondParam : Integer ; var ThirdParam : String ; var FourthParam : String);
    procedure CheckFlaot(value : String);
    procedure CheckStr(value : String);
    function CalcNewMACAddress(CurrMACAddress:string;CurrAllocQty:Integer) : String;
  public
    { Public declarations }
    procedure AllocateMACAddress; overload;
    procedure AllocateMACAddress(numOfRepetition,Offset : string) ; overload;

    function qry001_GetCurrMAC():String;
    function q002_get_idnumber_data(idnumber: String):String;
    function sp001_mac_address_alloc(P_MODE: String ; P_TRACE_ID: string; P_SERIAL: string; P_ID_NUMBER_ID: string; P_ALLOC_QTY: string; P_FILE_VERSION: string):TStringArray;  //; P_ERROR: string; P_RETURN_MAK_ADDRESS: string):String;


  end;

var
  dmGeneral: TdmGeneral;

implementation


{$R *.dfm}

const
  //serverURL: String = 'http://localhost:8080/MacRegREST/MacRegExt/ws/';

   //serverURL: String = 'http://webservices01:8080/MacRegREST/MacReg/Qry/';     //itzik local
  //serverURL: String = 'http://localhost:8080/MacRegREST/MacReg/Qry/';     //itzik local
    // Production in DMZ

   serverURL: String = 'http://ws-proxy01.rad.com:10211/MacRegREST/MacRegExt/ws/';  //external Prod

   // new Production on webservices03
   // serverURL: String = 'http://192.168.24.66:8080/MacRegREST/MacReg/Qry/';   internal Prod
   //serverURL: String = 'http://192.168.24.64:8080/MacRegREST/MacRegExt/ws/';     //Ext Test on webservices01


{ TdmGeneral }

procedure TdmGeneral.AllocateMACAddress; /// line 97 is continue?

/// add CH on left side of Temp upto Len
function Lpad(Temp:String;const CH:char;Len:Integer):String;
var
  StrL:integer;
begin
	Strl:=Length(Temp);
	if Strl<Len then result:=StringOfChar(CH,Len-Strl)+Temp
    else Result:=Copy(Temp,1,Len);
end;


function CalControlDigit(BarCode:String):integer;
var
	i:integer;
	Temp:Integer;
begin
	Temp:=0;
	for i:=1 to Length(BarCode) do
		if i/2 = int(i/2) then
			Temp:=Temp+StrToInt(Barcode[i])
		else
			Temp:=Temp+StrToInt(Barcode[i])*3;
	Temp:=10-Temp mod 10;
	if Temp = 10 then result:=0 else result:=Temp;
end;


var
  MACQty,Mode,L : Integer;
  FileName,Trac,Serial,IdNumber,OldMAC_Address,NewMAC_Address,FileVersion,ErrorMessage,tmp : String;
  MACFileHandle: TextFile;
  Id_Numbers_Id : Double;
  DBResult : TStringArray;
begin
  Success := 0;
  Trac := '';
  Serial := '';
  IdNumber := '';
  FileVersion := '';
  Mode := StrToInt(ParamStr(1)); /// we use 0
  SetLength(DBResult, 2);
  case Mode Of
    0 : begin // First Param ParamStr(0) - Type Id = 0 -> None
          MACQty := StrToInt(ParamStr(2));  
          FileName := ParamStr(3);
          FileVersion := ParamStr(4);  /// we use 1
        end;
    1 : begin // First Param ParamStr(0) - Type Id = 1 -> Traceability
          InsertValuesToVar(Trac,MACQty,FileName,FileVersion); ///  ParamStr(2)->Trac, ParamStr(3)->MACQty, ParamStr(4)->FileName, ParamStr(5)->FileVersion
          try
            CheckFlaot(Trac);  /// Trac -> StrToFloat
          except
            Success := 5;
          end;
        end;
    2 : begin // First Param ParamStr(0) - Type Id = 2 -> Serial
          InsertValuesToVar(Serial,MACQty,FileName,FileVersion); /// ParamStr(2)->Serial, ParamStr(3)->MACQty, ParamStr(4)->FileName, ParamStr(5)->FileVersion
          try
            CheckFlaot(Serial);
          except
            Success := 6;
          end;
        end;
    3 : begin // First Param ParamStr(0) - Type Id = 3 -> Id Number
          InsertValuesToVar(IdNumber,MACQty,FileName,FileVersion); /// ParamStr(2)->IdNumber, ParamStr(3)->MACQty, ParamStr(4)->FileName, ParamStr(5)->FileVersion
          try
            CheckStr(IdNumber); /// IdNumber -> StrToInt
            Success := 7;
          except
            Success := 0;
          end;
        end;
  end;

  /// output file
  try
    AssignFile(MACFileHandle,FileName);
    Rewrite(MACFileHandle);
  except
    ShowMessage('Can Not Create Output File!');
    exit;
  end;

  Id_Numbers_Id := 0;
  if (IdNumber <> '') then
  begin
    L := Length(IdNumber);
    if (L<8) then
     IdNumber:=LPad(IdNumber,'0',8)  ; /// put zeros in left side until IdNumber's len == 8
    else if (L>12) then
    begin
      IdNumber:=Copy(IdNumber,1,12); /// ??? if len > 12 -> take from second digit
    end;
	
	/// if len == 12 and last digit != CalculatedControlDigit 
    if (L>11)and(StrToInt(Copy(IdNumber,Length(IdNumber),1))<>CalControlDigit(cOPY(IdNumber,4,Length(IdNumber)-4))) then
    begin
      Success := 3;
    end
    else
    begin
      //qry002_GetIdNumberData.Close;
      //qry002_GetIdNumberData.ParamByName('P_ID_NUMBER').AsString := IdNumber;
      //qry002_GetIdNumberData.Open;
      //Id_Numbers_Id := qry002_GetIdNumberDataID.AsFloat;
      //qry002_GetIdNumberData.Close;
      Id_Numbers_Id := strtofloat(q002_get_idnumber_data(IdNumber));  /// returns "id": 17297868  for DC10023311315
    end;
  end;

  if MACQty > 48 then Success := 8;

  if Success = 0 then
  begin
    //Get New MAC Address - Select For Update Look MAC_ENUMERATE table.
   // qry001_GetCurrMAC_Address.Close;
   // qry001_GetCurrMAC_Address.Open;
   // OldMAC_Address := qry001_GetCurrMAC_AddressMAC_ADDRESS.AsString;
   // qry001_GetCurrMAC_Address.Close;

  //  OldMAC_Address :=   qry001_GetCurrMAC();

  //  NewMAC_Address := CalcNewMACAddress(OldMAC_Address,MACQty);

   // sp001_MAC_ADDRES_ALLOC.ParamByName('P_MODE').AsFloat := Mode;

//    if Trac = '' then
//      sp001_MAC_ADDRES_ALLOC.ParamByName('P_TRACE_ID').Clear
//    else
//      sp001_MAC_ADDRES_ALLOC.ParamByName('P_TRACE_ID').AsFloat := StrToFloat(Trac);
//
//    if Serial = '' then
//      sp001_MAC_ADDRES_ALLOC.ParamByName('P_SERIAL').Clear
//    else
//      sp001_MAC_ADDRES_ALLOC.ParamByName('P_SERIAL').AsFloat := StrToFloat(Serial);

//    if IdNumber = '' then
//      sp001_MAC_ADDRES_ALLOC.ParamByName('P_ID_NUMBER_ID').Clear
//    else
//      sp001_MAC_ADDRES_ALLOC.ParamByName('P_ID_NUMBER_ID').AsFloat := Id_Numbers_Id;
//
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_ALLOC_QTY').AsFloat := MACQty;
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_FILE_VERSION').AsString := FileVersion;
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_MAC_ADDRESS').AsString := NewMAC_Address;
//    sp001_MAC_ADDRES_ALLOC.Execute;
//
//    Success := sp001_MAC_ADDRES_ALLOC.ParamByName('P_ERROR').AsInteger;

    DBResult := sp001_mac_address_alloc(inttostr(Mode), Trac, Serial, floattostr(Id_Numbers_Id), inttostr(MACQty), FileVersion);
    Success :=  strtoint(DBResult[0]);
    tmp :=   DBResult[1];
  end;
  case Success of
  //  0 : Writeln(MACFilehandle,Format('%S',[sp001_MAC_ADDRES_ALLOC.ParamByName('P_RETURN_MAK_ADDRESS').AsString + ' '+ IntToStr(MACQty)]));
    0 : Writeln(MACFilehandle,Format('%S',[tmp + ' '+ IntToStr(MACQty)]));
    1 : begin
          case Mode of
            1 : ErrorMessage := 'Traceability Id ';
            2 : ErrorMessage := 'Serial Number';
            3 : ErrorMessage := 'Id Number ';
          end;
          ErrorMessage := ErrorMessage + 'Do Not Exist Error';
          Writeln(MACFilehandle,Format('%S',['ERROR' + ' '+ ErrorMessage]));
        end;
    2 : Writeln(MACFilehandle,Format('%S',['ERROR Genral Error']));
    3 : Writeln(MACFilehandle,Format('%S',['ERROR Id Number Control Digit Wrong']));
    4 : Writeln(MACFilehandle,Format('%S',['ERROR MAC Qty Undefined']));
    5 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Traceability Id']));
    6 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Serial Number']));
    7 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Id Number']));
    8 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Mac Qty']));
  end;
  Closefile(MACFileHandle);
end;

procedure TdmGeneral.AllocateMACAddress(numOfRepetition, Offset:  string);
var
  numOfRep , oSet   : Integer;
  NewMAC_Address , OldMAC_Address,file_Name : String;
  MACFileHandle : TextFile;
  DBResult : TStringArray;
begin
  SetLength(DBResult, 2);
  try

    if not SaveDialog1.Execute then
      exit;

    file_Name := SaveDialog1.FileName;
    AssignFile(MACFileHandle,file_Name);
    Rewrite(MACFileHandle);
  except
    ShowMessage('Can Not Create Output File!');
    exit;
  end;
  //Check if Number Of Repetition is valid integer value;
  try
    numOfRep := StrToInt(numOfRepetition);
  except
    MessageDlg('Number Of Repetition is invalid integer value,Please Insert integer value only',mtError,[mbOK],0);
  end;

  //Check if MAC Address Allocation Offset is valid integer value;
  try
    oSet := StrToInt(Offset);
  except
    MessageDlg('MAC Address Allocation Offset is invalid integer value,Please Insert integer value only',mtError,[mbOK],0);
  end;

  While numOfRep >=  1 do
  begin
    //Get New MAC Address - Select For Update Look MAC_ENUMERATE table.
   // qry001_GetCurrMAC_Address.Close;
   // qry001_GetCurrMAC_Address.Open;
   // OldMAC_Address := qry001_GetCurrMAC_AddressMAC_ADDRESS.AsString;
   // qry001_GetCurrMAC_Address.Close;
  //  OldMAC_Address :=   qry001_GetCurrMAC();
  //  NewMAC_Address := CalcNewMACAddress(OldMAC_Address,oSet);

//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_MODE').AsFloat := 0;
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_TRACE_ID').Clear;
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_SERIAL').Clear;
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_ID_NUMBER_ID').Clear;
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_ALLOC_QTY').AsFloat := oSet;
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_FILE_VERSION').AsString := '1';
//    sp001_MAC_ADDRES_ALLOC.ParamByName('P_MAC_ADDRESS').AsString := NewMAC_Address;

 //   sp001_MAC_ADDRES_ALLOC.Execute;

 //   Success := sp001_MAC_ADDRES_ALLOC.ParamByName('P_ERROR').AsInteger;

    DBResult := sp001_mac_address_alloc('0', '' , '', '', inttostr(oSet), '1');
    Success :=  strtoint(DBResult[0]);
    case Success of
      0 : Writeln(MACFilehandle,Format('%S',[NewMAC_Address + ' '+ IntToStr(oSet)]));
      2 : Writeln(MACFilehandle,Format('%S',['ERROR Genral Error']));
      3 : Writeln(MACFilehandle,Format('%S',['ERROR Id Number Control Digit Wrong']));
      4 : Writeln(MACFilehandle,Format('%S',['ERROR MAC Qty Undefined']));
      5 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Traceability Id']));
      6 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Serial Number']));
      7 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Id Number']));
      8 : Writeln(MACFilehandle,Format('%S',['ERROR Illegal Mac Qty']));
    end;
    numOfRep := numOfRep -1 ;
  end;
  Closefile(MACFileHandle);
end;


function TdmGeneral.CalcNewMACAddress(CurrMACAddress: string;
  CurrAllocQty: Integer): String;
function HexToInt(HexStr: String):Longint;
begin
  result := StrToInt('$' + HexStr);
end;
begin
  /// currMacAddress = 1856AB123EFE
  /// allocQty = 10
  ///       1856A                                       B123EFE
  ///                                          185,745,150
  ///                                  185,745,150 -10 = 185,745,140      
  ///                                  B12 3EF4  
  ///       1856AB123EF4
  Result := Copy(CurrMACAddress,1,5)+ IntToHex(HexToInt(Copy(CurrMACAddress,6,7))-CurrAllocQty,0);
end;

procedure TdmGeneral.CheckFlaot(value: String);
begin
  StrToFloat(value);
end;

procedure TdmGeneral.CheckStr(value: String);
begin
  StrToInt(value);
end;

procedure TdmGeneral.InsertValuesToVar(var FirstParam: String;
  var SecondParam: Integer; var ThirdParam, FourthParam: String);
begin
  FirstParam := ParamStr(2);
  try
    SecondParam := StrToInt(ParamStr(3));
  except
    SecondParam := 0;
    Success := 4;
  end;
  ThirdParam := ParamStr(4);
  FourthParam := ParamStr(5);
end;

 
 function TdmGeneral.qry001_GetCurrMAC():String;
var
   currentMAC: String;
   StringStream:  TStringStream;
   wsResult: String;
   obj: ISuperObject;
   AMember,  OMember: IMember;
   Asc : Byte;
  i : Integer;
begin
    {**
      qry001_GetCurrMAC_ will get the mac from DB :

    **}
   // Result := 0;
    StringStream := TStringStream.Create('');
    wsResult := IdHTTP1.Post(serverURL+'q001_get_current_mac', StringStream); /// python-לא הצלחתי ב ולא ב-פוסטמן
    obj := SO(wsResult);



    If ((wsResult <> '' )  and (Length(wsResult) > 0 ) )then
     begin

     for AMember in obj.A['q001_get_current_mac'] do
      begin

        for OMember in AMember.AsObject do
          begin

               If ( OMember.Name = 'mac_address') then
               begin
                  currentMAC := OMember.ToString;
                  currentMAC := Copy(currentMAC,2,12); // remove " from string in json
               end;
          end;


   end;
   end;
   result :=  currentMAC;
end;

function TdmGeneral.q002_get_idnumber_data(idnumber: String):String;
var
   id: String;
   StringStream:  TStringStream;
   wsResult: String;
   obj: ISuperObject;
   AMember,  OMember: IMember;
   Asc : Byte;
  i : Integer;
begin
    {**
      qry001_GetCurrMAC_ will get the mac from DB :

    **}
    //Result := true;
    StringStream := TStringStream.Create('idnumber='+idnumber);
    wsResult := IdHTTP1.Post(serverURL+'q002_get_idnumber_data', StringStream);  /// !!! python-כן הצלחתי ב
    obj := SO(wsResult);



    If ((wsResult <> '' )  and (Length(wsResult) > 0 ) )then
     begin

     for AMember in obj.A['q002_get_idnumber_data'] do
      begin

        for OMember in AMember.AsObject do
          begin

               If ( OMember.Name = 'id') then
                  id := OMember.ToString;
          end;


   end;
   end;
   result := id;
end;

function TdmGeneral.sp001_mac_address_alloc(P_MODE: String ; P_TRACE_ID: string; P_SERIAL: string; P_ID_NUMBER_ID: string; P_ALLOC_QTY: string; P_FILE_VERSION: string ):TStringArray;
var
   p_error: String;
   return_MAC_Address: String;

   StringStream:  TStringStream;
   wsResult: String;
   obj: ISuperObject;
   AMember,  OMember: IMember;
   Asc : Byte;
  i : Integer;
  DBResult : TStringArray; //array[2] of string;
begin
    {**
      sp001_mac_address_alloc will get  :

    **}
    SetLength(DBResult, 2);
    StringStream := TStringStream.Create('p_mode='+p_mode+'&p_trace_id='+p_trace_id+'&p_serial='+p_serial+'&p_idnumber_id='+p_id_number_id+'&p_alloc_qty='+p_alloc_qty+'&p_file_version='+p_file_version);
    wsResult := IdHTTP1.Post(serverURL+'sp001_mac_address_alloc', StringStream);
    obj := SO(wsResult);



    If ((wsResult <> '' )  and (Length(wsResult) > 0 ) )then
     begin

     for AMember in obj.A['sp001_mac_address_alloc'] do
      begin

        for OMember in AMember.AsObject do
          begin

               If ( OMember.Name = 'Error') then
               begin
                  p_error := OMember.ToString;
                  p_error := Copy(p_error,2,1); // remove " from string in json - copy just one digit
               end;

               If ( OMember.Name = 'New_MAC_Address') then
               begin
                  return_MAC_Address := OMember.ToString;
                  return_MAC_Address := Copy(return_MAC_Address,2,12); // remove " from string in json
               end;
          end;
   end;
   end;

   If p_error <> '' Then
      DBResult[0] := p_error;

    If return_MAC_Address <> '' Then
      DBResult[1] := return_MAC_Address;

   result := DBResult;
end;


end.
