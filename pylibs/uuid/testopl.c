#include "dav_opaquelock.h"

int main()
{
    uuid_state st;
    uuid_t u;
    const char *lt;

    dav_create_uuid_state(&st);
    dav_create_opaquelocktoken(&st, &u);
    lt = dav_format_opaquelocktoken(&u);
    printf("lt = %s\n", lt);
    free(lt);
}
	
