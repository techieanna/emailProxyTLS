CREATE OR REPLACE PROCEDURE srk_import_ad (
    var_ldap_path IN VARCHAR2,
    var_type      IN VARCHAR2
) AS

    l_ldap_host                    VARCHAR2(256) := 'CORP0.AD0.srk.NET';
    l_ldap_port                    VARCHAR2(256) := '636';
    l_ldap_user                    VARCHAR2(256) := 'CN=d12122c,OU=Service Users,OU=User Accounts,DC=corp0,DC=ad0,DC=srk,DC=net';
    l_ldap_passwd                  VARCHAR2(256) := '34343434';
    l_ldap_base                    VARCHAR2(256) := 'OU=Solid Users,OU=User Accounts,DC=corp0,DC=ad0,DC=srk,DC=net';
    rtype                          CHAR(1) := 'E';
    l_retval                       PLS_INTEGER;
    l_session                      dbms_ldap.session;
    l_attrs                        dbms_ldap.string_collection;
    l_message                      dbms_ldap.message;
    l_entry                        dbms_ldap.message;
    l_attr_name                    VARCHAR2(256);
    l_ber_element                  dbms_ldap.ber_element;
    l_vals                         dbms_ldap.string_collection;
    var_oprid                      VARCHAR2(256);
    var_company                    VARCHAR2(256);
    var_department                 VARCHAR2(256);
    var_givenname                  VARCHAR2(256);
    var_postalcode                 VARCHAR2(256);
    var_streetaddress              VARCHAR2(256);
    var_c                          VARCHAR2(256);
    var_co                         VARCHAR2(256);
    var_countrycode                VARCHAR2(256);
    var_departmentnumber           VARCHAR2(256);
    var_displayname                VARCHAR2(256);
    var_division                   VARCHAR2(256);
    var_employeeid                 VARCHAR2(256);
    var_employeetype               VARCHAR2(256);
    var_facsimiletelephonenumber   VARCHAR2(256);
    var_l                          VARCHAR2(256);
    var_manager                    VARCHAR2(256);
    var_mobile                     VARCHAR2(256);
    var_physicaldeliveryofficename VARCHAR2(256);
    var_srkbusinessarea            VARCHAR2(256);
    var_srkbusinessunit            VARCHAR2(256);
    var_sn                         VARCHAR2(256);
    var_telephonenumber            VARCHAR2(256);
    var_dn                         VARCHAR2(256);
    var_distinguishedname          VARCHAR2(256);
    var_ldap_path_int              VARCHAR2(256);
    var_type_int                   VARCHAR2(256);
    sql_stmt                       VARCHAR2(200);
    var_position                   NUMBER;
    var_position2                  NUMBER;
    emplid_count                   NUMBER;
    search_string                  VARCHAR2(256);
BEGIN
    dbms_ldap.use_exception := true;
    var_ldap_path_int := var_ldap_path;
    IF var_ldap_path_int IS NULL OR var_ldap_path_int = ' ' OR var_ldap_path_int = '' THEN
        var_ldap_path_int := l_ldap_base;
    END IF;

    IF var_type IS NULL OR var_type = ' ' THEN
        var_type_int := 'GBL';
    ELSE
        var_type_int := var_type;
    END IF;

    sql_stmt := 'DELETE from ps_srk_ad_import where TYPENAME = :1';
    EXECUTE IMMEDIATE sql_stmt
        USING var_type_int;
    l_session := dbms_ldap.init(hostname => l_ldap_host, portnum => l_ldap_port);
    l_retval := dbms_ldap.open_ssl(l_session, 'file:/opt/app/oracle/admin/H9200SD2/h92_wallet', 'rokirokiPakiPaKy6589_edbKas2', 3);
    l_retval := dbms_ldap.simple_bind_s(ld => l_session, dn => l_ldap_user, passwd => l_ldap_passwd);

    l_attrs(1) := 'Company';
    l_attrs(2) := 'Department';
    l_attrs(3) := 'GivenName';
    l_attrs(4) := 'PostalCode';
    l_attrs(5) := 'StreetAddress';
    l_attrs(6) := 'c';
    l_attrs(7) := 'co';
    l_attrs(8) := 'countryCode';
    l_attrs(9) := 'departmentNumber';
    l_attrs(10) := 'displayName';
    l_attrs(11) := 'division';
    l_attrs(12) := 'employeeID';
    l_attrs(13) := 'employeeType';
    l_attrs(14) := 'facsimileTelephoneNumber';
    l_attrs(15) := 'l';
    l_attrs(16) := 'manager';
    l_attrs(17) := 'mobile';
    l_attrs(18) := 'physicalDeliveryOfficeName';
    l_attrs(19) := 'srkBusinessArea';
    l_attrs(20) := 'srkBusinessUnit';
    l_attrs(21) := 'sn';
    l_attrs(22) := 'telephoneNumber';
    l_attrs(23) := 'name';
    l_attrs(24) := 'distinguishedName';
    emplid_count := 0;
    WHILE emplid_count < 1000 LOOP
        search_string := 'employeeID='
                         || lpad(emplid_count, 3, '0')
                         || '*';
        dbms_output.put_line('count' || search_string);
        l_retval := dbms_ldap.search_s(ld => l_session, base => var_ldap_path_int, scope => dbms_ldap.scope_subtree, filter => search_string,
        attrs => l_attrs,
                                      attronly => 0, res => l_message);

        IF dbms_ldap.count_entries(ld => l_session, msg => l_message) > 0 THEN
            l_entry := dbms_ldap.first_entry(ld => l_session, msg => l_message);
            WHILE l_entry IS NOT NULL LOOP
                var_oprid := ' ';
                var_dn := ' ';
                var_company := ' ';
                var_department := ' ';
                var_givenname := ' ';
                var_postalcode := ' ';
                var_streetaddress := ' ';
                var_c := ' ';
                var_co := ' ';
                var_countrycode := ' ';
                var_departmentnumber := '  ';
                var_displayname := ' ';
                var_division := ' ';
                var_employeeid := '
';
                var_employeetype := ' ';
                var_facsimiletelephonenumber := ' ';
                var_l := ' ';
                var_manager := ' ';
                var_mobile := '  ';
                var_physicaldeliveryofficename := ' ';
                var_srkbusinessarea := ' ';
                var_srkbusinessunit := ' ';
                var_sn := ' ';
                var_telephonenumber := ' ';
                var_dn := dbms_ldap.get_dn(ld => l_session, ldapentry => l_entry);
                var_distinguishedname := ' ';
                var_position := instr(var_dn, 'CN=', 1, 1);
                var_position2 := instr(var_dn, ',OU=', 1, 1);
                var_dn := substr(var_dn, var_position + 3, var_position2 - 3 - var_position);
                -- Limit var_dn to 30 characters before insertion
                var_dn := substr(var_dn, 1, 30);
                l_attr_name := dbms_ldap.first_attribute(ld => l_session, ldapentry => l_entry, ber_elem => l_ber_element);

                WHILE l_attr_name IS NOT NULL LOOP
                    l_vals := dbms_ldap.get_values(ld => l_session, ldapentry => l_entry, attr => l_attr_name);

                    FOR i IN l_vals.first..l_vals.last LOOP
                        IF l_attr_name = 'company' THEN
                            var_company := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'department' THEN
                            var_department := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'givenName' THEN
                            var_givenname := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'postalCode' THEN
                            var_postalcode := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'streetAddress' THEN
                            var_streetaddress := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'c' THEN
                            var_c := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'co' THEN
                            var_co := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'countryCode' THEN
                            var_countrycode := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'departmentNumber' THEN
                            var_departmentnumber := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'displayName' THEN
                            var_displayname := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'division' THEN
                            var_division := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'employeeID' THEN
                            var_employeeid := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'employeeType' THEN
                            var_employeetype := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'facsimileTelephoneNumber' THEN
                            var_facsimiletelephonenumber := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'l' THEN
                            var_l := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'manager' THEN
                            var_manager := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'mobile' THEN
                            var_mobile := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'physicalDeliveryOfficeName' THEN
                            var_physicaldeliveryofficename := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'srkBusinessArea' THEN
                            var_srkbusinessarea := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'srkBusinessUnit' THEN
                            var_srkbusinessunit := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'sn' THEN
                            var_sn := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'telephoneNumber' THEN
                            var_telephonenumber := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'name' THEN
                            var_oprid := substr(l_vals(i), 1, 200);
                        ELSIF l_attr_name = 'distinguishedName' THEN
                            var_distinguishedname := substr(l_vals(i), 1, 200);
                        END IF;
                    END LOOP values_loop;

                    l_attr_name := dbms_ldap.next_attribute(ld => l_session, ldapentry => l_entry, ber_elem => l_ber_element);

                END LOOP attibutes_loop;

                INSERT INTO ps_srk_ad_import (
                    oprid,
                    srk_ad_company,
                    srk_ad_dept,
                    first_name,
                    postal,
                    address1,
                    country2,
                    country_descr,
                    socs_cntry_cd_esp,
                    deptid,
                    srk_name_display,
                    srk_legal_descr2,
                    emplid,
                    per_org,
                    srk_fax_phone,
                    city,
                    dsdn,
                    srk_cel_phone,
                    office_name,
                    srk_legal_descr3,
                    srk_legal_descr4,
                    last_name,
                    srk_bsn_phone,
                    typename,
                    dsdn_empl
                ) VALUES (
                    var_dn,
                    var_company,
                    var_department,
                    var_givenname,
                    var_postalcode,
                    var_streetaddress,
                    var_c,
                    var_co,
                    var_countrycode,
                    var_departmentnumber,
                    var_displayname,
                    var_division,
                    var_employeeid,
                    var_employeetype,
                    var_facsimiletelephonenumber,
                    var_l,
                    var_manager,
                    var_mobile,
                    var_physicaldeliveryofficename,
                    var_srkbusinessarea,
                    var_srkbusinessunit,
                    var_sn,
                    var_telephonenumber,
                    var_type_int,
                    var_distinguishedname
                );

                l_entry := dbms_ldap.next_entry(ld => l_session, msg => l_entry);
            END LOOP entry_loop;

        END IF;

        emplid_count := emplid_count + 1;
    END LOOP emplid_loop;

    l_retval := dbms_ldap.unbind_s(ld => l_session);
END;
/
